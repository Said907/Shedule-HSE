import pytest
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

def message_mock():
    return MagicMock()


def test_get_id(message_mock):
    message_mock.text = 'SomeGroup'
    with patch('schedule.sqlite3.connect') as mock_connect:
        with patch('schedule.sqlite3.Cursor') as mock_cursor:
            get_id(message_mock)
            mock_cursor.execute.assert_called_with("SELECT groupid FROM grup WHERE grnm = ?", ('SomeGroup',))


