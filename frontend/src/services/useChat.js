import axios from 'axios';

export async function postChatQuery(query) {
    try {
        const response = await axios.post('http://localhost:8000/api/chat/query', { ...query });
        return response.data;
    } catch (error) {
        console.error('Error posting chat query:', error);
        throw error;
    }
}