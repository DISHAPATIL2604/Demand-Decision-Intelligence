import { useEffect, useState } from "react";

import {
  uploadSalesFile,
  getUploads,
} from "../../services/api";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [uploads, setUploads] = useState([]);

 
  const loadUploads = async () => {
    try {
      const data = await getUploads();
      setUploads(data.uploads || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadUploads();
  }, []);


  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    setError("");
    setResult(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Please select a CSV file.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  
  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file first.");
      return;
    }

    try {
      setUploading(true);
      setError("");
      setResult(null);

      const data = await uploadSalesFile(file);

      setResult(data);

     
      await loadUploads();

      
      setFile(null);

    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 space-y-8">

      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold">
          Data Upload
        </h1>

        <p className="text-gray-500 mt-2">
          Upload sales data and validate it before
          storing it in the database.
        </p>
      </div>

      {/* Upload Box */}
      <div className="border rounded-xl p-6 bg-white shadow-sm">

        <h2 className="text-xl font-semibold mb-4">
          Upload Sales CSV
        </h2>

        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="block w-full border rounded-lg p-3"
        />

        {file && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p>
              <strong>Selected file:</strong>{" "}
              {file.name}
            </p>

            <p className="text-sm text-gray-500">
              Size:{" "}
              {(file.size / 1024).toFixed(2)} KB
            </p>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="mt-4 px-5 py-3 rounded-lg bg-black text-white disabled:opacity-50"
        >
          {uploading
            ? "Uploading..."
            : "Upload CSV"}
        </button>

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 rounded-lg bg-red-50 text-red-700">
            ❌ {error}
          </div>
        )}

      </div>

      {/* Upload Result */}
      {result && (
        <div className="border rounded-xl p-6 bg-white shadow-sm">

          <h2 className="text-xl font-semibold mb-4">
            Upload Result
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">
                Status
              </p>
              <p className="font-bold">
                {result.status}
              </p>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">
                Total Rows
              </p>
              <p className="font-bold">
                {result.total_rows}
              </p>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">
                Valid Rows
              </p>
              <p className="font-bold">
                {result.valid_rows}
              </p>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">
                Invalid Rows
              </p>
              <p className="font-bold">
                {result.invalid_rows}
              </p>
            </div>

          </div>

          {/* Validation */}
          {result.validation && (
            <div className="mt-6">

              <h3 className="font-semibold mb-3">
                Validation Summary
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

                {Object.entries(
                  result.validation
                ).map(([key, value]) => (
                  <div
                    key={key}
                    className="border rounded-lg p-3"
                  >
                    <p className="text-sm text-gray-500">
                      {key.replaceAll("_", " ")}
                    </p>

                    <p className="font-semibold">
                      {value}
                    </p>
                  </div>
                ))}

              </div>

            </div>
          )}

        </div>
      )}

      {/* Upload History */}
      <div className="border rounded-xl p-6 bg-white shadow-sm">

        <h2 className="text-xl font-semibold mb-4">
          Upload History
        </h2>

        {uploads.length === 0 ? (
          <p className="text-gray-500">
            No uploads found.
          </p>
        ) : (
          <div className="overflow-x-auto">

            <table className="w-full text-left">

              <thead>
                <tr className="border-b">
                  <th className="p-3">
                    File
                  </th>

                  <th className="p-3">
                    Status
                  </th>

                  <th className="p-3">
                    Total Rows
                  </th>

                  <th className="p-3">
                    Processed
                  </th>
                </tr>
              </thead>

              <tbody>

                {uploads.map((upload) => (
                  <tr
                    key={upload.id}
                    className="border-b"
                  >
                    <td className="p-3">
                      {upload.filename}
                    </td>

                    <td className="p-3">
                      {upload.status}
                    </td>

                    <td className="p-3">
                      {upload.total_rows}
                    </td>

                    <td className="p-3">
                      {upload.processed_rows}
                    </td>
                  </tr>
                ))}

              </tbody>

            </table>

          </div>
        )}

      </div>

    </div>
  );
}