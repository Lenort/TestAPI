<?php
// index.php — точка входа

$message = '';
if (isset($_GET['result'])) {
    if ($_GET['result'] === 'success') {
        $message = 'Ваша заявка отправлена!';
    } elseif ($_GET['result'] === 'error') {
        $message = 'Произошла ошибка при создании лида.';
    }
}

include __DIR__ . '/templates/form.php';
