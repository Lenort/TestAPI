<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Оставить заявку</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">

    <style>
        body {
            font-family: 'Montserrat', sans-serif;
            background: linear-gradient(to bottom right, #f2f2f2, #e0e0e0);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }

        .lead-form {
            background-color: #ffffff;
            padding: 30px 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 500px;
            position: relative;
        }

        .lead-form h1 {
            font-size: 24px;
            margin-bottom: 20px;
            text-align: center;
            color: #333333;
        }

        label {
            font-weight: 600;
            display: block;
            margin: 15px 0 5px;
        }

        input[type="text"],
        select {
            width: 100%;
            padding: 10px;
            border: 1px solid #cccccc;
            border-radius: 6px;
            box-sizing: border-box;
            font-size: 16px;
        }

        button {
            width: 100%;
            padding: 12px;
            margin-top: 20px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        button:hover {
            background-color: #0056b3;
        }

        .message {
            padding: 10px;
            margin-top: 20px;
            border-radius: 6px;
            text-align: center;
        }

        .message.success {
            background-color: #d4edda;
            color: #155724;
        }

        .message.error {
            background-color: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>

<form method="post" action="process.php" class="lead-form">
    <h1>Оставить заявку в Битрикс24</h1>

    <label for="fio">ФИО</label>
    <input type="text" id="fio" name="fio" required value="<?php echo htmlspecialchars($_POST['fio'] ?? ''); ?>" />

    <label for="city">Город</label>
    <select id="city" name="city" required>
        <option value="">Выберите город</option>
        <option value="Астана" <?php if (($_POST['city'] ?? '') == 'Астана') echo 'selected'; ?>>Астана</option>
        <option value="Алматы" <?php if (($_POST['city'] ?? '') == 'Алматы') echo 'selected'; ?>>Алматы</option>
        <option value="Караганда" <?php if (($_POST['city'] ?? '') == 'Караганда') echo 'selected'; ?>>Караганда</option>
        <option value="Шымкент" <?php if (($_POST['city'] ?? '') == 'Шымкент') echo 'selected'; ?>>Шымкент</option>
        <option value="Павлодар" <?php if (($_POST['city'] ?? '') == 'Павлодар') echo 'selected'; ?>>Павлодар</option>
    </select>

    <label for="direction">Направление</label>
    <select id="direction" name="direction" required>
        <option value="">Выберите направление</option>
        <option value="Лаки" <?php if (($_POST['direction'] ?? '') == 'Лаки') echo 'selected'; ?>>Лаки</option>
        <option value="Краски" <?php if (($_POST['direction'] ?? '') == 'Краски') echo 'selected'; ?>>Краски</option>
        <option value="Грунтовки" <?php if (($_POST['direction'] ?? '') == 'Грунтовки') echo 'selected'; ?>>Грунтовки</option>
        <option value="Растворители" <?php if (($_POST['direction'] ?? '') == 'Растворители') echo 'selected'; ?>>Растворители</option>
    </select>

    <label for="phone">Телефон</label>
    <input type="text" id="phone" name="phone" required value="<?php echo htmlspecialchars($_POST['phone'] ?? ''); ?>" />

    <button type="submit">Отправить заявку</button>

    <?php if (!empty($message)): ?>
        <div class="message <?php echo ($message === 'Заявка успешно отправлена!') ? 'success' : 'error'; ?>">
            <?php echo htmlspecialchars($message); ?>
        </div>
    <?php endif; ?>
</form>

</body>
</html>
