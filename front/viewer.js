/*
 * Usage:
 *
 *    const viewer = new Viewer('canvas', 'img/composite.png', [{
 *      bounds: [0, 0, 50, 50],
 *      onEnter: () => {
 *        console.log('enter');
 *      },
 *      onLeave: () => {
 *        console.log('leave');
 *      }
 *    }]);
 *
 */

const dpr = window.devicePixelRatio || 1;

class Viewer {
  constructor(id, imgurl, objects) {
    this.canvas = document.getElementById(id);
    this.ctx = canvas.getContext('2d');
    this.ctx.imageSmoothingEnabled = false;

    this.pan = {x: 0, y: 0};
    window.onresize = () => this.resize();
    this.resize();

    this.img = new Image();
    this.img.onload = () => this.draw();
    this.img.src = imgurl;

    // Interactive/collision objects
    this.objects = objects || [];

    // Panning
    let dragging = false;
    let start = {x: null, y: null};
    let rect = this.canvas.getBoundingClientRect();
    this.offset = {x: rect.left, y: rect.top};
    this.focused = [];
    this.canvas.addEventListener('mousedown', (ev) => {
      dragging = true;
      start = {
        x: parseInt(ev.clientX - this.offset.x),
        y: parseInt(ev.clientY - this.offset.y)
      };
    });
    this.canvas.addEventListener('mouseup', () => dragging = false)
    this.canvas.addEventListener('mouseleave', () => dragging = false)
    this.canvas.addEventListener('mousemove', (ev) => {
      let mouse = {
        x: parseInt(ev.clientX - this.offset.x),
        y: parseInt(ev.clientY - this.offset.y)
      };

      if (dragging) {
        let dx = mouse.x - start.x;
        let dy = mouse.y - start.y;
        start = mouse;
        this.pan.x += dx;
        this.pan.y += dy;
        this.ctx.translate(dx, dy);
        this.draw();

      } else {
        // Translate mouse coordinates to canvas coordinates
        let pos = {
          x: mouse.x - this.pan.x,
          y: mouse.y - this.pan.y
        };
        let focused = [];
        this.objects.forEach((obj) => {
          if (pos.x >= obj.bounds[0]/dpr && pos.x <= obj.bounds[2]/dpr
            && pos.y >= obj.bounds[1]/dpr && pos.y <= obj.bounds[3]/dpr) {
            if (!this.focused.includes(obj)) {
              obj.onEnter();
            }
            focused.push(obj);
          }
        });
        this.focused.filter(o => !focused.includes(o)).forEach((obj) => obj.onLeave());
        this.focused = focused;
      }
    });
  }

  resize() {
    // Get 'natural' parent node dimensions
    this.canvas.style.display = 'none';
    let rect = {
      width: this.canvas.parentNode.offsetWidth,
      height: this.canvas.parentNode.offsetHeight
    };
    this.canvas.style.display = 'block';

    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = `${rect.width}px`;
    this.canvas.style.height = `${rect.height}px`;
    this.ctx.scale(dpr, dpr);
    this.ctx.translate(this.pan.x, this.pan.y);
    this.draw();
  }

  draw() {
    this.ctx.save();
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.ctx.restore();
    if (this.img && this.img.complete) {
      this.ctx.drawImage(this.img, 0, 0, this.img.width/dpr, this.img.height/dpr);
    }
  }
}