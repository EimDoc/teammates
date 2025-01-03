from __future__ import annotations

import uuid
from typing import Optional

from fastapi import UploadFile, Body, Request, APIRouter

from src.models.models import QuestionnaireOut, QuestionnaireIn
from src.entities.entities import DBEntities
from src.utils.utils import save_questionnaire_image

questionnaire_router = APIRouter(
    prefix="/questionnaire",
)


@questionnaire_router.post(
    '',
    response_model=Optional[QuestionnaireOut],
)
async def post_questionnaire(
        request: Request,
        questionnaire_in: QuestionnaireIn = Body(...),
        image: Optional[UploadFile] = None,
) -> Optional[QuestionnaireOut]:
    questionnaire_id = uuid.uuid4()
    image_path = await save_questionnaire_image(image, questionnaire_id, str(request.url))
    response_questionnaire = await DBEntities.questionnaires_db.add_questionnaire(
        questionnaire_in, image_path, questionnaire_id
    )
    return response_questionnaire
