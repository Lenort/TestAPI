<?php
// user.php — ручной модуль, вызывается только напрямую

$url = 'https://b24-q1r4u7.bitrix24.kz/rest/1/2v6q3jv9k428rphg/user.get.json';

$curl = curl_init();
curl_setopt_array($curl, [
    CURLOPT_URL => $url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_SSL_VERIFYPEER => false,
]);

$response = curl_exec($curl);
curl_close($curl);

$data = json_decode($response, true);

echo "<h2>Список пользователей Bitrix24:</h2>";

if (!empty($data['result'])) {
    echo "<ul>";
    foreach ($data['result'] as $user) {
        $id = htmlspecialchars($user['ID']);
        $name = htmlspecialchars($user['NAME']);
        $lastName = htmlspecialchars($user['LAST_NAME']);
        $email = htmlspecialchars($user['EMAIL']);
        echo "<li>ID: $id, Имя: $name, Фамилия: $lastName, Email: $email</li>";
    }
    echo "</ul>";
} else {
    echo "<p>Не удалось получить список пользователей.</p>";
    if (isset($data['error_description'])) {
        echo "<p>Ошибка: " . htmlspecialchars($data['error_description']) . "</p>";
    }
}
