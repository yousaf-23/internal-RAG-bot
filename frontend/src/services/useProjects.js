import axios from 'axios';

export async function getProjectsQuery() {
    try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/api/projects`);
        return response.data;
    } catch (error) {
        console.error('Error posting chat query:', error);
        throw error;
    }
}

export async function AddProjects(newProject) {
    try {
        const response = await axios.post(`${process.env.REACT_APP_API_URL}/api/projects`, newProject);
        return response.data;
    } catch (error) {
        console.error('Error posting chat query:', error);
        throw error;
    }
}
export async function DeleteProjects({project_id}) {
    try {
        const response = await axios.delete(`${process.env.REACT_APP_API_URL}/api/projects/${project_id}`);
        return response.data;
    } catch (error) {
        console.error('Error posting chat query:', error);
        throw error;
    }
}