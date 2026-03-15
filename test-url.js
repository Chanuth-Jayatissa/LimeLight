import fetch from 'node-fetch';
async function test() {
  const res = await fetch('https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3', { method: 'HEAD' });
  console.log(res.status);
}
test();
