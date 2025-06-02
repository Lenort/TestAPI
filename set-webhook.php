<?php
// --- 1. Отправляем PATCH запрос для установки вебхука ---
$ch = curl_init("https://api.wazzup24.com/v3/webhooks");

$data = [
    "webhooksUri" => "https://desan.lovestoblog.com/webhook.php",
    "subscriptions" => [
        [
            "channel" => "whatsapp",
            "subscriptions" => ["message", "status"]
        ]
    ]
];

curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "PATCH");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Authorization: Bearer 92a8247c0ce7472a86a5c36f71327d19",
    "Content-Type: application/json"
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// --- 2. Выводим ответ Wazzup ---
echo "<h2>Ответ Wazzup ($httpCode):</h2><pre>" . htmlspecialchars($response) . "</pre>";

// --- 3. Выводим содержимое лога вебхука ---
$logFile = __DIR__ . '/wazzup-log.txt';

echo "<h2>Лог вебхука (последние 100 строк):</h2>";

if (file_exists($logFile)) {
    $logContent = file($logFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $lastLines = array_slice($logContent, -100);
    echo "<pre>" . htmlspecialchars(implode("\n", $lastLines)) . "</pre>";
} else {
    echo "<p>Файл лога не найден.</p>";
}
