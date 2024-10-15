const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const axios = require('axios');
const app = express();
const server = http.createServer(app);
const io = new Server(server);

const OPENAI_API_KEY = 'your-openai-api-key-here'; // Replace with your OpenAI API Key

app.use(express.static('public')); // Serve frontend

let humanSocketId = null;
let testSocketId = null;

io.on('connection', (socket) => {
  console.log('a user connected:', socket.id);

  socket.on('register', (type) => {
    if (type === 'human') {
      humanSocketId = socket.id;
      console.log('Human connected:', humanSocketId);
    } else if (type === 'tester') {
      testSocketId = socket.id;
      console.log('Tester connected:', testSocketId);
    }
  });

  // Relay messages to both human and ChatGPT
  socket.on('message', async (msg) => {
    if (socket.id === testSocketId) {
      // Send the message to both the human participant and ChatGPT
      if (humanSocketId) {
        io.to(humanSocketId).emit('message', msg);
      }

      // Get a response from ChatGPT
      const gptResponse = await getChatGPTResponse(msg);
      io.to(testSocketId).emit('response', { source: 'chatgpt', message: gptResponse });
    } else if (socket.id === humanSocketId) {
      // Human participant responds
      io.to(testSocketId).emit('response', { source: 'human', message: msg });
    }
  });

  socket.on('disconnect', () => {
    console.log('user disconnected:', socket.id);
  });
});

// Function to call OpenAI's ChatGPT API
async function getChatGPTResponse(message) {
  try {
    const response = await axios.post('https://api.openai.com/v1/completions', {
      model: 'text-davinci-003',
      prompt: message,
      max_tokens: 150,
    }, {
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`
      }
    });

    return response.data.choices[0].text.trim();
  } catch (error) {
    console.error('Error with OpenAI API:', error);
    return 'Error: Unable to connect to ChatGPT';
  }
}

server.listen(3000, () => {
  console.log('Server is listening on port 3000');
});
