/** File metadata returned by the FastAPI file endpoints. */
export interface FileInfo {
  file_id: string;
  file_name: string;
  status: "processing" | "ready" | "failed";
  error_message: string | null;
  created_at: string;
}
