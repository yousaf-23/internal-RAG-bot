import axios from 'axios';

export async function postChatQuery(query) {
    try {
        const response = await axios.post(`${process.env.REACT_APP_API_URL}/api/chat/query`, { ...query });
        return response.data;
    } catch (error) {
        console.error('Error posting chat query:', error);
        throw error;
    }
}

export async function getChatHistory({project_id}) {
    try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/api/chat/history/${project_id}`);
        return response.data;
    } catch (error) {
        console.error('Error posting chat feedback:', error);
        throw error;
    }
}