from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).parents[1] / "app.py"


def test_app_answers_locally_and_adds_task_only_after_confirmation(
	monkeypatch,
) -> None:
	monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
	app = AppTest.from_file(str(APP_PATH)).run()

	app.selectbox[0].select("cat")
	app.text_input[2].set_value("cat scratching post")
	app.button[0].click().run()

	assert not app.exception
	answer = app.session_state["pet_care_answer"]
	assert answer.status == "answered"
	assert "Offer cats appropriate places to scratch" in answer.answer
	assert any(button.label == "Add task to schedule" for button in app.button)

	app.text_input(key="answer_based_task_description").set_value(
		"Set up a scratching post"
	)
	add_task_button = next(
		button for button in app.button if button.label == "Add task to schedule"
	)
	add_task_button.click().run()

	assert not app.exception
	owner = app.session_state["owner"]
	assert [task.description for task in owner.pets[0].tasks] == [
		"Set up a scratching post"
	]


def test_medical_question_shows_veterinary_referral_without_task_form(
	monkeypatch,
) -> None:
	monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
	app = AppTest.from_file(str(APP_PATH)).run()

	app.text_input[2].set_value("Why is my cat vomiting?")
	app.button[0].click().run()

	assert not app.exception
	assert app.session_state["pet_care_answer"].status == "veterinary_referral"
	assert "contact your veterinarian" in app.warning[0].value.lower()
	assert all(button.label != "Add task to schedule" for button in app.button)
