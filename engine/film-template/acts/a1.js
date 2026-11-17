// One act = one file. build() makes the DOM once; seek(u) draws second u of this act and nothing else decides the picture.
// Something must move on every frame: a picture held for 0.4 s fails the freeze gate.
Film.act('a1', {
  build(root) {
    root.innerHTML = '<svg viewBox="0 0 1080 1920" width="1080" height="1920"><circle cx="540" cy="960" r="90" fill="#CC3333"/></svg>';
    this.dot = root.querySelector('circle');
  },
  seek(u) {
    this.dot.setAttribute('cx', 240 + 300 * u);
    this.dot.setAttribute('r', 90 + 30 * Math.sin(u * 6));
  },
});
