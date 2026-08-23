const express = require('express');
const axios = require('axios');

const app = express();
const PORT = 3000;

app.get('/', (req, res) => {
  res.send('Hello from P008 test app!');
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
