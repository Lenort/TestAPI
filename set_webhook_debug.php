<?php
$logFile = __DIR__ . '/wazzup-log.txt';

if (file_exists($logFile)) {
    $content = htmlspecialchars(file_get_contents($logFile));
    echo "<pre>$content</pre>";
} else {
    echo "Файл лога пока не создан.";
}
