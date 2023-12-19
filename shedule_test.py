import unittest
from unittest.mock import MagicMock, patch
from shedule import (
    get_id,
    ask_course,
    ask_group,
    handle_start,
    handle_messages,
    ask_for_note,
    save_note,
    save_note_to_database,
    show_notes,
    ask_combined_filter_params,
    process_combined_filter_params,
    ask_for_day,
    get_selected_day,
    show_subjects,
    show_filter_keyboard,
    ask_for_lesson_id_filter,
    get_lesson_by_id,
    filter_lessons_by_id,
    show_subject_filter,
    handle_subject_filter_lecturer,
    show_lecturer_filter,
    handle_subject_filter_subject,
    show_date_filter,
    process_date_filter_response,
    show_lesson_type_filter,
    process_lesson_type_choices,
    filter_lessons_by_type,
    answerempty,
    send_filtered_lessons,
)

class TestScheduleBot(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_id(self):
        message_mock = MagicMock()
        message_mock.text = 'SomeGroup'
        with patch('schedule.sqlite3.connect') as mock_connect:
            with patch('schedule.sqlite3.Cursor') as mock_cursor:
                get_id(message_mock)
                mock_cursor.execute.assert_called_with("SELECT groupid FROM grup WHERE grnm = ?", ('SomeGroup',))

    def test_ask_course(self):
        message_mock = MagicMock()
        message_mock.from_user.id = 123  # Replace with a valid user ID
        with patch('schedule.types.ReplyKeyboardMarkup') as mock_reply_keyboard_markup:
            with patch('schedule.types.KeyboardButton') as mock_keyboard_button:
                ask_course(message_mock)

                mock_keyboard_button.assert_called_with('Курс 1')
                mock_reply_keyboard_markup.assert_called_once()

                message_mock.from_user.id.assert_called_with('Привет! Выбери свой курс:')
                message_mock.reply_markup.assert_called_once()

    def test_ask_group(self):
        message_mock = MagicMock()
        message_mock.text = 'Курс 1'
        with patch('schedule.sqlite3.connect') as mock_connect:
            with patch('schedule.sqlite3.Cursor') as mock_cursor:
                with patch('schedule.types.ReplyKeyboardMarkup') as mock_reply_keyboard_markup:
                    with patch('schedule.types.KeyboardButton') as mock_keyboard_button:
                        ask_group(message_mock)

                        mock_cursor.execute.assert_called_with("SELECT grnm FROM grup WHERE id = ?", (1,))

                        mock_keyboard_button.assert_called_with(text='GroupName1')
                        mock_reply_keyboard_markup.assert_called_once()

                        message_mock.from_user.id.assert_called_with('Выберите группу:')
                        message_mock.reply_markup.assert_called_once()

    def test_handle_start(self):
        message_mock = MagicMock()
        with patch('schedule.ask_course') as mock_ask_course:
            handle_start(message_mock)

            mock_ask_course.assert_called_with(message_mock)

    def test_handle_messages(self):
        message_mock = MagicMock()
        message_mock.text = 'Расписание'

        with patch('schedule.show_schedule_keyboard') as mock_show_schedule_keyboard:
            handle_messages(message_mock)

            mock_show_schedule_keyboard.assert_called_with(message_mock)

    def test_ask_for_note(self):
        message_mock = MagicMock()

        with patch('schedule.bot.send_message') as mock_send_message:
            ask_for_note(message_mock)

            mock_send_message.assert_called_with(message_mock.from_user.id, 'Введите id урока для записи заметки:')

    def test_save_note(self):
        message_mock = MagicMock()
        message_mock.text = 'LessonID123'

        with patch('schedule.bot.send_message') as mock_send_message:
            with patch('schedule.bot.register_next_step_handler') as mock_register_next_step_handler:
                save_note(message_mock)

                mock_send_message.assert_called_with(message_mock.from_user.id, 'Введите заметку:')

                mock_register_next_step_handler.assert_called_with(
                    message_mock,
                    lambda msg: save_note_to_database('LessonID123', message_mock.from_user.id, msg.text, message_mock)
                )

    def test_save_note_to_database(self):
        message_mock = MagicMock()

        with patch('schedule.sqlite3.connect') as mock_connect:
            with patch('schedule.sqlite3.Cursor') as mock_cursor:
                with patch('schedule.bot.send_message') as mock_send_message:
                    save_note_to_database('LessonID123', 123, 'This is a note.', message_mock)

                    mock_cursor.execute.assert_called_with(
                        'INSERT INTO note (lesson_id, user_id, note_text) VALUES (?, ?, ?)',
                        ('LessonID123', 123, 'This is a note.')
                    )

                    mock_connect.commit.assert_called_once()

                    mock_send_message.assert_called_with(message_mock.from_user.id, 'Выберите действие:')

    def test_show_notes(self):
        message_mock = MagicMock()
        message_mock.from_user.id = 123

        with patch('schedule.sqlite3.connect') as mock_connect:
            with patch('schedule.sqlite3.Cursor') as mock_cursor:
                with patch('schedule.bot.send_message') as mock_send_message:
                    mock_cursor.fetchall.return_value = [('LessonID123', 'This is a note.')]

                    show_notes(message_mock)

                    mock_cursor.execute.assert_called_with(
                        'SELECT lesson_id, note_text FROM note WHERE user_id = ?',
                        (123,)
                    )

                    mock_send_message.assert_called_with(
                        message_mock.from_user.id,
                        'Ваши заметки:\nLessonID123: This is a note.'
                    )

    def test_ask_combined_filter_params(self):
        message_mock = MagicMock()

        with patch('schedule.bot.send_message') as mock_send_message:
            with patch('schedule.bot.register_next_step_handler') as mock_register_next_step_handler:
                ask_combined_filter_params(message_mock)

                mock_send_message.assert_called_with(
                    message_mock.from_user.id,
                    'Введите параметры для комбинированного фильтра (через запятую): Преподаватель,Предмет,Дата,Тип занятий (введите от 2 до 4 параметров)'
                )

                mock_register_next_step_handler.assert_called_with(message_mock, process_combined_filter_params)

    def test_process_combined_filter_params(self):
        message_mock = MagicMock()
        message_mock.text = 'Преподаватель: Иванов, Предмет: Математика, Дата: 2023.01.01, Тип занятий: Лекция'

        with patch('schedule.bot.send_message') as mock_send_message:
            with patch('schedule.bot.show_filter_keyboard') as mock_show_filter_keyboard:
                with patch('schedule.get_all_lesson_types_lecturer') as mock_get_all_lesson_types_lecturer:
                    with patch('schedule.get_all_lesson_types_subject') as mock_get_all_lesson_types_subject:
                        with patch('schedule.get_all_lesson_types_date') as mock_get_all_lesson_types_date:
                            with patch('schedule.filter_lessons_by_type') as mock_filter_lessons_by_type:
                                process_combined_filter_params(message_mock)

                                mock_get_all_lesson_types_lecturer.assert_called_with('Иванов')
                                mock_get_all_lesson_types_subject.assert_called_with('Математика')
                                mock_get_all_lesson_types_date.assert_called_with('2023.01.01')
                                mock_filter_lessons_by_type.assert_called_with('Лекция')

                                mock_send_message.assert_called_with(
                                    message_mock.from_user.id,
                                    'Отфильтрованные данные по типу занятий "Преподаватель: Иванов, Предмет: Математика, Дата: 2023.01.01, Тип занятий: Лекция":\n'
                                    '-----------------------------------------------------\n'
                                    '...'
                                )

                                mock_show_filter_keyboard.assert_called_with(message_mock)

    def test_ask_for_day(self):
        message_mock = MagicMock()

        with patch('schedule.types.ReplyKeyboardMarkup') as mock_reply_keyboard_markup:
            with patch('schedule.types.KeyboardButton') as mock_keyboard_button:
                with patch('schedule.bot.send_message') as mock_send_message:
                    with patch('schedule.bot.register_next_step_handler') as mock_register_next_step_handler:
                        ask_for_day(message_mock)

                        mock_reply_keyboard_markup.assert_called_with(resize_keyboard=True)

                        mock_keyboard_button.assert_called_with('Понедельник')
                        mock_reply_keyboard_markup.add.assert_called_with(mock_keyboard_button.return_value)

                        mock_send_message.assert_called_with(
                            message_mock.from_user.id,
                            'Выберите день:',
                            reply_markup=mock_reply_keyboard_markup.return_value
                        )

                        mock_register_next_step_handler.assert_called_with(message_mock, get_selected_day)

    def test_get_selected_day(self):
        message_mock = MagicMock()
        message_mock.text = 'Понедельник'

        with patch('schedule.show_subjects') as mock_show_subjects:
            get_selected_day(message_mock)

            mock_show_subjects.assert_called_with(message_mock)

    def test_show_subjects(self):
        message_mock = MagicMock()

        with patch('schedule.schedule') as mock_schedule:
            with patch('schedule.types.ReplyKeyboardMarkup') as mock_reply_keyboard_markup:
                with patch('schedule.types.KeyboardButton') as mock_keyboard_button:
                    with patch('schedule.bot.send_message') as mock_send_message:
                        show_subjects(message_mock)

                        mock_reply_keyboard_markup.assert_called_with(resize_keyboard=True)

                        mock_keyboard_button.assert_called_with('Subject1')
                        mock_reply_keyboard_markup.add.assert_called_with(mock_keyboard_button.return_value)

                        mock_send_message.assert_called_with(
                            message_mock.from_user.id,
                            'Выберите предмет на Понедельник для просмотра расписания:',
                            reply_markup=mock_reply_keyboard_markup.return_value
                        )

    def test_show_filter_keyboard(self):
        message_mock = MagicMock()

        with patch('schedule.types.ReplyKeyboardMarkup') as mock_reply_keyboard_markup:
            with patch('schedule.types.KeyboardButton') as mock_keyboard_button:
                with patch('schedule.bot.send_message') as mock_send_message:
                    show_filter_keyboard(message_mock)

                    mock_reply_keyboard_markup.assert_called_with(resize_keyboard=True)

                    mock_keyboard_button.assert_called_with('Фильтр по преподу')
                    mock_reply_keyboard_markup.add.assert_called_with(mock_keyboard_button.return_value)

                    mock_send_message.assert_called_with(
                        message_mock.from_user.id,
                        'Выберите фильтр:',
                        reply_markup=mock_reply_keyboard_markup.return_value
                    )

    def test_ask_for_lesson_id_filter(self):
        message_mock = MagicMock()

        with patch('schedule.types.ReplyKeyboardRemove') as mock_reply_keyboard_remove:
            with patch('schedule.bot.send_message') as mock_send_message:
                with patch('schedule.bot.register_next_step_handler') as mock_register_next_step_handler:
                    ask_for_lesson_id_filter(message_mock)

                    mock_reply_keyboard_remove.assert_called_with()

                    mock_send_message.assert_called_with(
                        message_mock.from_user.id,
                        'Введите ID урока для фильтрации:',
                        reply_markup=mock_reply_keyboard_remove.return_value
                    )

                    mock_register_next_step_handler.assert_called_with(message_mock, filter_lessons_by_id)

    def test_get_lesson_by_id(self):
        lesson_id = '202312345678'
        expected_lesson = {'date': '2023.01.01', 'kindOfWork': 'Лекция', 'discipline': 'Математика',
                           'lecturer': 'Иванов',
                           'group': 'Group1', 'auditorium': '101', 'beginLesson': '10:00', 'endLesson': '11:30'}

        with patch('schedule.data', new_callable=PropertyMock) as mock_data:
            mock_data.__getitem__.return_value = {'Lessons': [expected_lesson]}

            result = get_lesson_by_id(lesson_id)

            assert result == expected_lesson

    def test_filter_lessons_by_id(self):
        message_mock = MagicMock()
        message_mock.text = '202312345678'

        with patch('schedule.get_lesson_by_id') as mock_get_lesson_by_id:
            with patch('schedule.send_filtered_lessons') as mock_send_filtered_lessons:
                with patch('schedule.show_filter_keyboard') as mock_show_filter_keyboard:
                    filter_lessons_by_id(message_mock)

                    mock_get_lesson_by_id.assert_called_with(message_mock.text)

                    mock_send_filtered_lessons.assert_called_with(message_mock, [mock_get_lesson_by_id.return_value])

                    mock_show_filter_keyboard.assert_called_with(message_mock)

    def test_show_subject_filter(self):
        message_mock = MagicMock()

        with patch('schedule.types.ReplyKeyboardRemove') as mock_reply_keyboard_remove:
            with patch('schedule.bot.send_message') as mock_send_message:
                with patch('schedule.bot.register_next_step_handler') as mock_register_next_step_handler:
                    show_subject_filter(message_mock)

                    mock_reply_keyboard_remove.assert_called_with()

                    mock_send_message.assert_called_with(
                        message_mock.from_user.id,
                        'Введите имя преподавателя для фильтрации:',
                        reply_markup=mock_reply_keyboard_remove.return_value
                    )

                    mock_register_next_step_handler.assert_called_with(message_mock, handle_subject_filter_lecturer)

    def test_handle_subject_filter_lecturer(self):
        message_mock = MagicMock()
        message_mock.text = 'Иванов'

        with patch('schedule.get_all_lesson_types_lecturer') as mock_get_all_lesson_types_lecturer:
            with patch('schedule.send_filtered_lessons') as mock_send_filtered_lessons:
                with patch('schedule.show_schedule_keyboard') as mock_show_schedule_keyboard:
                    handle_subject_filter_lecturer(message_mock)

                    mock_get_all_lesson_types_lecturer.assert_called_with(message_mock.text)

                    mock_send_filtered_lessons.assert_called_with(message_mock,
                                                                  mock_get_all_lesson_types_lecturer.return_value)

                    mock_show_schedule_keyboard.assert_called_with(message_mock)

    def test_show_lecturer_filter(self):
        message_mock = MagicMock()

        with patch('schedule.types.ReplyKeyboardRemove') as mock_reply_keyboard_remove:
            with patch('schedule.bot.send_message') as mock_send_message:
                with patch('schedule.bot.register_next_step_handler') as mock_register_next_step_handler:
                    show_lecturer_filter(message_mock)

                    mock_reply_keyboard_remove.assert_called_with()

                    mock_send_message.assert_called_with(
                        message_mock.from_user.id,
                        'Введите имя предмет для фильтрации:',
                        reply_markup=mock_reply_keyboard_remove.return_value
                    )

                    mock_register_next_step_handler.assert_called_with(message_mock, handle_subject_filter_subject)

    def test_handle_subject_filter_subject(self):
        message_mock = MagicMock()
        message_mock.text = 'Математика'

        with patch('schedule.get_all_lesson_types_subject') as mock_get_all_lesson_types_subject:
            with patch('schedule.send_filtered_lessons') as mock_send_filtered_lessons:
                with patch('schedule.show_schedule_keyboard') as mock_show_schedule_keyboard:
                    handle_subject_filter_subject(message_mock)

                    mock_get_all_lesson_types_subject.assert_called_with(message_mock.text)

                    mock_send_filtered_lessons.assert_called_with(message_mock,
                                                                  mock_get_all_lesson_types_subject.return_value)

                    mock_show_schedule_keyboard.assert_called_with(message_mock)

    def test_show_date_filter(self):
        message_mock = MagicMock()

        with patch('schedule.types.ReplyKeyboardMarkup') as mock_reply_keyboard_markup:
            with patch('schedule.types.KeyboardButton') as mock_keyboard_button:
                with patch('schedule.bot.send_message') as mock_send_message:
                    with patch('schedule.bot.register_next_step_handler') as mock_register_next_step_handler:
                        show_date_filter(message_mock)

                        mock_reply_keyboard_markup.assert_called_with(resize_keyboard=True, one_time_keyboard=False)

                        mock_keyboard_button.assert_called_with('Отмена')

                        mock_send_message.assert_called_with(
                            message_mock.from_user.id,
                            'Выберите дату для фильтрации:(В формате гггг.мм.дд)',
                            reply_markup=mock_reply_keyboard_markup.return_value
                        )

                        mock_register_next_step_handler.assert_called_with(message_mock, process_date_filter_response)

    def test_process_date_filter_response(self):
        message_mock = MagicMock()
        message_mock.text = '2023.12.31'

        with patch('schedule.get_all_lesson_types_date') as mock_get_all_lesson_types_date:
            with patch('schedule.send_filtered_lessons') as mock_send_filtered_lessons:
                with patch('schedule.show_schedule_keyboard') as mock_show_schedule_keyboard:
                    process_date_filter_response(message_mock)

                    mock_get_all_lesson_types_date.assert_called_with(message_mock.text)

                    mock_send_filtered_lessons.assert_called_with(message_mock,
                                                                  mock_get_all_lesson_types_date.return_value)

                    mock_show_schedule_keyboard.assert_called_with(message_mock)

    def test_show_lesson_type_filter(self):
        message_mock = MagicMock()

        with patch('schedule.types.ReplyKeyboardMarkup') as mock_reply_keyboard_markup:
            with patch('schedule.types.KeyboardButton') as mock_keyboard_button:
                with patch('schedule.bot.send_message') as mock_send_message:
                    with patch('schedule.bot.register_next_step_handler') as mock_register_next_step_handler:
                        show_lesson_type_filter(message_mock)

                        mock_reply_keyboard_markup.assert_called_with(resize_keyboard=True)

                        mock_keyboard_button.assert_has_calls([
                            call('Семинары'),
                            call('Лекция'),
                            call('Практика'),
                            call('Вернуться к фильтру'),
                            call('Экзамен')
                        ], any_order=True)

                        mock_send_message.assert_called_with(
                            message_mock.from_user.id,
                            'Выберите тип занятий для фильтрации:',
                            reply_markup=mock_reply_keyboard_markup.return_value
                        )

                        mock_register_next_step_handler.assert_called_with(message_mock, process_lesson_type_choices)

    def test_process_lesson_type_choices(self):
        message_mock = MagicMock()
        message_mock.text = 'Лекция'

        with patch('schedule.filter_lessons_by_type') as mock_filter_lessons_by_type:
            with patch('schedule.send_filtered_lessons') as mock_send_filtered_lessons:
                with patch('schedule.show_filter_keyboard') as mock_show_filter_keyboard:
                    process_lesson_type_choices(message_mock)

                    mock_filter_lessons_by_type.assert_called_with(message_mock.text)

                    mock_send_filtered_lessons.assert_called_with(message_mock,
                                                                  mock_filter_lessons_by_type.return_value)

                    mock_show_filter_keyboard.assert_called_with(message_mock)

    def test_filter_lessons_by_type():
        lesson_type = 'Лекция'
        data = {
            'Lessons': [
                {'kindOfWork': 'Лекция'},
                {'kindOfWork': 'Семинар'},
                {'kindOfWork': 'Практика'},
            ]
        }

        filtered_lessons = filter_lessons_by_type(lesson_type)

        assert len(filtered_lessons) == 1
        assert filtered_lessons[0]['kindOfWork'] == lesson_type

    def test_answerempty():
        message_mock = MagicMock()

        with patch('schedule.bot.send_message') as mock_send_message:
            answerempty(message_mock)

            mock_send_message.assert_called_with(
                message_mock.from_user.id,
                "В этот день у вас занятий нет"
            )

    def test_send_filtered_lessons():
        message_mock = MagicMock()
        filtered_lessons = [
            {'group': 'Группа1', 'discipline': 'Математика', 'kindOfWork': 'Лекция', 'lecturer': 'Преподаватель1'},
            {'group': 'Группа2', 'discipline': 'Физика', 'kindOfWork': 'Семинар', 'lecturer': 'Преподаватель2'}
        ]

        with patch('schedule.create_lesson_id') as mock_create_lesson_id:
            with patch('schedule.bot.send_message') as mock_send_message:
                with patch('schedule.bot.send_document') as mock_send_document:
                    send_filtered_lessons(message_mock, filtered_lessons)

                    mock_create_lesson_id.assert_called_with(filtered_lessons)

                    mock_send_message.assert_called_with(
                        message_mock.chat.id,
                        f'Отфильтрованные данные по типу занятий "{message_mock.text}":\n'
                        f'-----------------------------------------------------\n',
                        parse_mode='Markdown'
                    )

                    mock_send_document.assert_called_once()

                    assert mock_send_document.call_args[0][1].__enter__.called
                    assert mock_send_document.call_args[0][1].__exit__.called


if __name__ == '__main__':
    unittest.main()
