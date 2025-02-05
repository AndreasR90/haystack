from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import torch

from haystack.preview.dataclasses import Document
from haystack.preview.components import LocalWhisperTranscriber

from test.preview.components.base import BaseTestComponent


SAMPLES_PATH = Path(__file__).parent.parent.parent / "test_files"


class Test_LocalWhisperTranscriber(BaseTestComponent):
    @pytest.mark.unit
    def test_save_load(self, tmp_path):
        self.assert_can_be_saved_and_loaded_in_pipeline(
            LocalWhisperTranscriber(model_name_or_path="large-v2"), tmp_path
        )

    @pytest.mark.unit
    def test_init(self):
        transcriber = LocalWhisperTranscriber(
            model_name_or_path="large-v2"
        )  # Doesn't matter if it's huge, the model is not loaded in init.
        assert transcriber.model_name == "large-v2"
        assert transcriber.device == torch.device("cpu")
        assert transcriber._model is None

    @pytest.mark.unit
    def test_init_wrong_model(self):
        with pytest.raises(ValueError, match="Model name 'whisper-1' not recognized"):
            LocalWhisperTranscriber(model_name_or_path="whisper-1")

    @pytest.mark.unit
    def test_warmup(self):
        with patch("haystack.preview.components.audio.whisper_local.whisper") as mocked_whisper:
            transcriber = LocalWhisperTranscriber(model_name_or_path="large-v2")
            mocked_whisper.load_model.assert_not_called()
            transcriber.warm_up()
            mocked_whisper.load_model.assert_called_once_with("large-v2", device=torch.device(type="cpu"))

    @pytest.mark.unit
    def test_warmup_doesnt_reload(self):
        with patch("haystack.preview.components.audio.whisper_local.whisper") as mocked_whisper:
            transcriber = LocalWhisperTranscriber(model_name_or_path="large-v2")
            transcriber.warm_up()
            transcriber.warm_up()
            mocked_whisper.load_model.assert_called_once()

    @pytest.mark.unit
    def test_run_with_path(self):
        comp = LocalWhisperTranscriber(model_name_or_path="large-v2")
        comp._model = MagicMock()
        comp._model.transcribe.return_value = {
            "text": "test transcription",
            "other_metadata": ["other", "meta", "data"],
        }
        results = comp.run(audio_files=[SAMPLES_PATH / "audio" / "this is the content of the document.wav"])
        expected = Document(
            content="test transcription",
            metadata={
                "audio_file": SAMPLES_PATH / "audio" / "this is the content of the document.wav",
                "other_metadata": ["other", "meta", "data"],
            },
        )
        assert results["documents"] == [expected]

    @pytest.mark.unit
    def test_run_with_str(self):
        comp = LocalWhisperTranscriber(model_name_or_path="large-v2")
        comp._model = MagicMock()
        comp._model.transcribe.return_value = {
            "text": "test transcription",
            "other_metadata": ["other", "meta", "data"],
        }
        results = comp.run(
            audio_files=[str((SAMPLES_PATH / "audio" / "this is the content of the document.wav").absolute())]
        )
        expected = Document(
            content="test transcription",
            metadata={
                "audio_file": str((SAMPLES_PATH / "audio" / "this is the content of the document.wav").absolute()),
                "other_metadata": ["other", "meta", "data"],
            },
        )
        assert results["documents"] == [expected]

    @pytest.mark.unit
    def test_transcribe(self):
        comp = LocalWhisperTranscriber(model_name_or_path="large-v2")
        comp._model = MagicMock()
        comp._model.transcribe.return_value = {
            "text": "test transcription",
            "other_metadata": ["other", "meta", "data"],
        }
        results = comp.transcribe(audio_files=[SAMPLES_PATH / "audio" / "this is the content of the document.wav"])
        expected = Document(
            content="test transcription",
            metadata={
                "audio_file": SAMPLES_PATH / "audio" / "this is the content of the document.wav",
                "other_metadata": ["other", "meta", "data"],
            },
        )
        assert results == [expected]

    @pytest.mark.unit
    def test_transcribe_stream(self):
        comp = LocalWhisperTranscriber(model_name_or_path="large-v2")
        comp._model = MagicMock()
        comp._model.transcribe.return_value = {
            "text": "test transcription",
            "other_metadata": ["other", "meta", "data"],
        }
        results = comp.transcribe(
            audio_files=[open(SAMPLES_PATH / "audio" / "this is the content of the document.wav", "rb")]
        )
        expected = Document(
            content="test transcription",
            metadata={"audio_file": "<<binary stream>>", "other_metadata": ["other", "meta", "data"]},
        )
        assert results == [expected]
