import { useState, useRef, useEffect } from "react";

const API_URL = "http://127.0.0.1:8000";

function DocumentUpload() {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState("");

    const fileInputRef = useRef(null);
    const messageTimerRef = useRef(null);

    // Clear timer when component is removed
    useEffect(() => {
        return () => {
            if (messageTimerRef.current) {
                clearTimeout(messageTimerRef.current);
            }
        };
    }, []);

    const showMessage = (text) => {
        setMessage(text);

        // Clear previous timer
        if (messageTimerRef.current) {
            clearTimeout(messageTimerRef.current);
        }

        // Hide message after 3 seconds
        messageTimerRef.current = setTimeout(() => {
            setMessage("");
        }, 3000);
    };

    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];

        if (!selectedFile) {
            return;
        }

        if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
            showMessage("Only PDF files are supported.");
            return;
        }

        setFile(selectedFile);
        setMessage("");
    };

    const handleUpload = async () => {
        if (!file) {
            return;
        }

        setUploading(true);
        setMessage("");

        const formData = new FormData();

        formData.append("file", file);

        try {
            const response = await fetch(
                `${API_URL}/documents/upload`,
                {
                    method: "POST",
                    body: formData,
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Upload failed."
                );
            }

            showMessage(
                `${file.name} uploaded. Ingestion started.`
            );

            setFile(null);

            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }

        } catch (error) {
            showMessage(
                error.message || "Upload failed."
            );

        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="document-upload">

            <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                style={{ display: "none" }}
            />

            {/* Paperclip button */}
            <button
                type="button"
                className="upload-button"
                onClick={() =>
                    fileInputRef.current?.click()
                }
                disabled={uploading}
                title="Add PDF document"
            >
                📎
            </button>

            {/* Selected file */}
            {file && (
                <div className="selected-file">

                    <span className="selected-file-name">
                        {file.name}
                    </span>

                    <button
                        type="button"
                        className="upload-confirm-button"
                        onClick={handleUpload}
                        disabled={uploading}
                    >
                        {uploading
                            ? "Uploading..."
                            : "Upload"}
                    </button>

                </div>
            )}

            {/* Status message */}
            {message && (
                <span className="upload-message">
                    {message}
                </span>
            )}

        </div>
    );
}

export default DocumentUpload;