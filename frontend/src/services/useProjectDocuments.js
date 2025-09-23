import axios from 'axios';

export async function getProjectDocumentsQuery(project_id) {
    try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/api/documents/project/${project_id}`);
        return response.data;
    } catch (error) {
        console.error('Error posting chat query:', error);
        throw error;
    }
}
export async function uploadDocumentQuery({projectId,formData}) {
    try {
        const response = await axios.post(`${process.env.REACT_APP_API_URL}/api/documents/upload?project_id=${projectId}`, formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Accept': 'application/json'
                }
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error uploading document:', error);
        throw error;
    }
}


export async function deleteDocument(documentId) {
    try {
        const response = await axios.delete(`${process.env.REACT_APP_API_URL}/api/documents/${documentId}`);
        return response.data;
    }
    catch (error) {
        console.error('Error deleting document:', error);
        throw error;
    }
}
