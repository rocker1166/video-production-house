// Second act of the template: a square that turns and grows. Replace both acts with the film's own.
Film.act('a2', {
  build(root) {
    root.innerHTML = '<svg viewBox="0 0 1080 1920" width="1080" height="1920"><rect x="-120" y="-120" width="240" height="240" fill="#222222"/></svg>';
    this.box = root.querySelector('rect');
  },
  seek(u) {
    this.box.setAttribute('transform', 'translate(540 960) rotate(' + 90 * u + ') scale(' + (1 + 0.4 * u) + ')');
  },
});
