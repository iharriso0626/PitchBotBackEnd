const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 3000;

// Define the endpoint to interact with the Python model server
app.post('/generate', async (req, res) => {
    try {
        const { prompt } = req.body;

        // Update the Python server URL to the new port
        const pythonServerUrl = 'http://localhost:5001/generate';
        
        // Send the prompt to the Python server
        const response = await axios.post(pythonServerUrl, { prompt });
        const { text } = response.data;

        // Send the generated text back to the client
        res.json({ text });
    } catch (error) {
        res.status(500).json({ error: 'Error generating text' });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});