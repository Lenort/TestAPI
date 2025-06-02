<?php
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: index.php');
    exit;
}

$fio = trim($_POST['fio'] ?? '');
$city = trim($_POST['city'] ?? '');
$direction = trim($_POST['direction'] ?? '');
$phone = trim($_POST['phone'] ?? '');

if (!$fio || !$city || !$direction || !$phone) {
    header('Location: index.php?result=error');
    exit;
}

$fioParts = explode(' ', $fio);
$lastName = $fioParts[0] ?? '';
$name = $fioParts[1] ?? '';
$secondName = $fioParts[2] ?? '';

$responsibles = [
    'Караганда' => ['name' => 'Кирилл Костылев', 'phone' => '+77766961328', 'id' => 11],
    'Астана' => ['name' => '', 'phone' => '+77001234567', 'id' => 1],
];

$responsible = $responsibles[$city] ?? ['name' => 'не назначен', 'phone' => '', 'id' => 1];

$comment = "Направление: $direction";

$data = [
    'fields' => [
        'TITLE' => "Заявка с сайта от $fio",
        'NAME' => $name,
        'LAST_NAME' => $lastName,
        'SECOND_NAME' => $secondName,
        'ASSIGNED_BY_ID' => $responsible['id'],
        'ADDRESS_CITY' => $city,
        'COMMENTS' => $comment,
        'PHONE' => [
            ["VALUE" => $phone, "VALUE_TYPE" => "WORK"],
        ],
    ],
    'params' => [
        "REGISTER_SONET_EVENT" => "Y"
    ],
];

$queryURL = 'https://b24-q1r4u7.bitrix24.kz/rest/1/2v6q3jv9k428rphg/crm.lead.add.json';

$curl = curl_init();
curl_setopt_array($curl, [
    CURLOPT_URL => $queryURL,
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_POSTFIELDS => json_encode($data),
    CURLOPT_SSL_VERIFYPEER => false,
]);

$result = curl_exec($curl);
curl_close($curl);

$resultData = json_decode($result, true);

if (isset($resultData['result']) && $resultData['result'] > 0) {
    header('Location: index.php?result=success');
} else {
    header('Location: index.php?result=error');
}
exit;
