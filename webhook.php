<?php
// Файл для логирования
$logFile = __DIR__ . '/wazzup-log.txt';

// Получаем "сырое" тело запроса
$input = file_get_contents('php://input');

// Логируем в файл
file_put_contents($logFile, date('Y-m-d H:i:s') . " — Вебхук получен\n", FILE_APPEND);
file_put_contents($logFile, $input . "\n\n", FILE_APPEND);

// Выводим в браузер (если открыли напрямую или для отладки)
echo "<h1>Wazzup Webhook</h1>";
echo "<h2>Дата: " . date('Y-m-d H:i:s') . "</h2>";
echo "<h3>Сырые данные:</h3>";
echo "<pre>" . htmlspecialchars($input) . "</pre>";

// Отвечаем Wazzup
http_response_code(200);
echo "<p style='color:green;'>Ответ: OK</p>";
