<?php
$permission_code = 'YOUR_SECRET_CODE';
$ai_response = '';
$msg = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['permission']) || $_POST['permission'] !== $permission_code) {
        $msg = "Invalid permission code.";
    } else {
        // Handle file upload
        if (isset($_FILES['file']) && $_FILES['file']['error'] === UPLOAD_ERR_OK) {
            $upload_dir = '/filesearchfolder/document/';
            $upload_file = $upload_dir . basename($_FILES['file']['name']);
            if (move_uploaded_file($_FILES['file']['tmp_name'], $upload_file)) {
                $msg = "File uploaded successfully!";
            } else {
                $msg = "Failed to upload file.";
            }
        }
        // Handle chatbot query
        if (!empty($_POST['chatquery'])) {
            $query = escapeshellarg($_POST['chatquery']);
            $cmd = "python3 /filesearchfolder/filesearchutilityandexportcsvAIagent.py $query 2>&1";
            $ai_response = shell_exec($cmd);
        }
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>File Upload & AI Chatbot</title>
</head>
<body>
    <form method="POST" enctype="multipart/form-data">
        Permission code: <input type="password" name="permission" required><br>
        Upload file: <input type="file" name="file"><br>
        <button type="submit">Upload</button>
    </form>

    <form method="POST">
        Permission code: <input type="password" name="permission" required><br>
        Chatbot query: <input type="text" name="chatquery">
        <button type="submit">Ask</button>
    </form>

    <?php if (!empty($ai_response)): ?>
        <div><b>AI:</b> <?php echo nl2br(htmlspecialchars($ai_response)); ?></div>
    <?php endif; ?>

    <?php if (!empty($msg)): ?>
        <div><?php echo htmlspecialchars($msg); ?></div>
    <?php endif; ?>
</body>
</html>
