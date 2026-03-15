import fetch from 'node-fetch';
async function test() {
  const res = await fetch('https://ceexnffhr5wbwd4gny4hzo65k40zgutx.lambda-url.us-east-2.on.aws/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: "Hello world", voice_id: "test", name: "Founder" })
  });
  console.log(res.status);
  const text = await res.text();
  console.log(text);
}
test();
