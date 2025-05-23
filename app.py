# 영어 버전
# import os
# import logging
# import json
# from fastapi import FastAPI, HTTPException, Depends, Security
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from datetime import datetime
# from typing import List
# import openai
# from dotenv import load_dotenv
# from contextlib import asynccontextmanager
# import uvicorn  # 추가
#
# # 로깅 설정
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
# # 환경 변수 로드
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# API_KEY = os.getenv("API_KEY")
#
# if not OPENAI_API_KEY:
#     logger.error("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
#     raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
# if not API_KEY:
#     logger.error("API_KEY가 .env 파일에 설정되지 않았습니다.")
#     raise ValueError("API_KEY가 .env 파일에 설정되지 않았습니다.")
#
# # OpenAI 클라이언트 초기화
# openai.api_key = OPENAI_API_KEY
#
# # Lifespan 이벤트 핸들러
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logger.info("Starting FastAPI server on http://0.0.0.0:8000")
#     yield
#     logger.info("Shutting down FastAPI server")
#
# # FastAPI 앱 초기화
# app = FastAPI(lifespan=lifespan)
# security = HTTPBearer()
#
# # CORS 설정
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# # 요청 모델
# class ItineraryRequest(BaseModel):
#     destination: str
#     preferences: str
#     budget: int
#     pace: int
#     start_date: str
#     end_date: str
#
# # 응답 모델
# class Activity(BaseModel):
#     activity: str
#     time: str
#     description: str
#
# class DayItinerary(BaseModel):
#     day: int
#     activities: List[Activity]
#
# class ItineraryResponse(BaseModel):
#     itinerary: List[DayItinerary]
#
# # API 키 검증
# async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
#     logger.info("Verifying API key")
#     if credentials.credentials != API_KEY:
#         logger.warning("Invalid API key provided")
#         raise HTTPException(status_code=403, detail="Invalid API key")
#     return credentials.credentials
#
# @app.post("/api/generate-itinerary", response_model=ItineraryResponse)
# async def generate_itinerary(request: ItineraryRequest, api_key: str = Depends(verify_api_key)):
#     logger.info(f"Received request: {request.model_dump()}")
#     logger.info(f"Generating itinerary for {request.destination} from {request.start_date} to {request.end_date}")
#
#     try:
#         # 날짜 파싱
#         start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
#         end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
#         days = (end_date - start_date).days + 1
#
#         if days < 1:
#             logger.error("End date must be after start date")
#             raise HTTPException(status_code=400, detail="End date must be after start date")
#
#         # OpenAI 프롬프트 생성
#         prompt = f"""
#         Create a {days}-day travel itinerary for {request.destination}.
#         Preferences: {request.preferences}
#         Budget: {request.budget}/100 (0=low, 100=high)
#         Pace: {request.pace}/100 (0=relaxed, 100=intense)
#         Start date: {request.start_date}
#         End date: {request.end_date}
#
#         Return a valid JSON object with the following structure:
#         [
#             {{
#                 "day": 1,
#                 "activities": [
#                     {{
#                         "activity": "Activity name",
#                         "time": "morning|afternoon|lunch|evening",
#                         "description": "Description of the activity"
#                     }}
#                 ]
#             }}
#         ]
#         Ensure the response contains only the JSON object, with no additional text, markdown, backticks, or explanations.
#         """
#
#         # OpenAI API 호출
#         try:
#             response = openai.ChatCompletion.create(
#                 model="gpt-3.5-turbo",
#                 messages=[
#                     {"role": "system", "content": "You are a travel planner that responds with valid JSON only. Do not include markdown, backticks, or any text outside the JSON object."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.3,
#                 max_tokens=1500
#             )
#         except openai.error.AuthenticationError:
#             logger.error("Invalid OpenAI API key")
#             raise HTTPException(status_code=500, detail="Invalid OpenAI API key")
#         except openai.error.RateLimitError:
#             logger.error("OpenAI API rate limit exceeded")
#             raise HTTPException(status_code=500, detail="OpenAI API rate limit exceeded")
#         except openai.error.OpenAIError as e:
#             logger.error(f"OpenAI API error: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
#
#         # 응답 처리
#         raw_response = response.choices[0].message.content.strip()
#         logger.info(f"Raw OpenAI response: '{raw_response}'")
#
#         # JSON 파싱
#         try:
#             if not raw_response:
#                 logger.error("Empty response from OpenAI")
#                 raise HTTPException(status_code=500, detail="Empty response from OpenAI")
#             itinerary_data = json.loads(raw_response)
#         except json.JSONDecodeError as e:
#             logger.error(f"Failed to parse OpenAI response as JSON: {e}")
#             logger.error(f"Raw response: '{raw_response}'")
#             raise HTTPException(status_code=500, detail=f"Invalid JSON response from OpenAI: {e}")
#
#         # 응답 검증 및 변환
#         itinerary = []
#         for day_data in itinerary_data:
#             activities = [
#                 Activity(
#                     activity=activity["activity"],
#                     time=activity["time"],
#                     description=activity["description"]
#                 )
#                 for activity in day_data["activities"]
#             ]
#             itinerary.append(DayItinerary(day=day_data["day"], activities=activities))
#
#         return ItineraryResponse(itinerary=itinerary)
#
#     except Exception as e:
#         logger.error(f"Error generating itinerary: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
#
# if __name__ == "__main__":
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# ======================================================================================================================================================
# 한국어
import os
import logging
import json
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List
import openai
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_KEY = os.getenv("API_KEY")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://travelling.p-e.kr").split(",")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
if not API_KEY:
    logger.error("API_KEY가 .env 파일에 설정되지 않았습니다.")
    raise ValueError("API_KEY가 .env 파일에 설정되지 않았습니다.")

# OpenAI 클라이언트 초기화
openai.api_key = OPENAI_API_KEY

# Lifespan 이벤트 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FastAPI server on http://0.0.0.0:5000")
    yield
    logger.info("Shutting down FastAPI server")

# FastAPI 앱 초기화
app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 모델
class ItineraryRequest(BaseModel):
    destination: str
    preferences: str
    budget: int
    pace: int
    start_date: str
    end_date: str

# 응답 모델
class Activity(BaseModel):
    activity: str
    time: str
    description: str

class DayItinerary(BaseModel):
    day: int
    activities: List[Activity]

class ItineraryResponse(BaseModel):
    itinerary: List[DayItinerary]

# API 키 검증
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    logger.info("Verifying API key")
    if credentials.credentials != API_KEY:
        logger.warning("Invalid API key provided")
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials

@app.post("/api/generate-itinerary", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryRequest, api_key: str = Depends(verify_api_key)):
    logger.info(f"Received request: {request.model_dump()}")
    logger.info(f"Generating itinerary for {request.destination} from {request.start_date} to {request.end_date}")

    try:
        # 날짜 파싱
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        days = (end_date - start_date).days + 1

        if days < 1:
            logger.error("End date must be after start date")
            raise HTTPException(status_code=400, detail="End date must be after start date")

        # OpenAI 프롬프트 생성
        prompt = f"""
        Create a {days}-day travel itinerary for {request.destination}.
        Preferences: {request.preferences}
        Budget: {request.budget}/100 (0=low, 100=high)
        Pace: {request.pace}/100 (0=relaxed, 100=intense)
        Start date: {request.start_date}
        End date: {request.end_date}

        All activity names and descriptions must be written in Korean. Use natural and idiomatic Korean language for activities and descriptions.
        Return a valid JSON object with the following structure:
        [
            {{
                "day": 1,
                "activities": [
                    {{
                        "activity": "활동 이름 (한국어)",
                        "time": "morning|afternoon|lunch|evening",
                        "description": "활동 설명 (한국어)"
                    }}
                ]
            }}
        ]
        Ensure the response contains only the JSON object, with no additional text, markdown, backticks, or explanations.
        """

        # OpenAI API 호출
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel planner that responds with valid JSON only. All activity names and descriptions must be in Korean. Do not include markdown, backticks, or any text outside the JSON object."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
        except openai.error.AuthenticationError:
            logger.error("Invalid OpenAI API key")
            raise HTTPException(status_code=500, detail="Invalid OpenAI API key")
        except openai.error.RateLimitError:
            logger.error("OpenAI API rate limit exceeded")
            raise HTTPException(status_code=500, detail="OpenAI API rate limit exceeded")
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

        # 응답 처리
        raw_response = response.choices[0].message.content.strip()
        logger.info(f"Raw OpenAI response: '{raw_response}'")

        # JSON 파싱
        try:
            if not raw_response:
                logger.error("Empty response from OpenAI")
                raise HTTPException(status_code=500, detail="Empty response from OpenAI")
            itinerary_data = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Raw response: '{raw_response}'")
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from OpenAI: {e}")

        # 응답 검증 및 변환
        itinerary = []
        for day_data in itinerary_data:
            activities = [
                Activity(
                    activity=activity["activity"],
                    time=activity["time"],
                    description=activity["description"]
                )
                for activity in day_data["activities"]
            ]
            itinerary.append(DayItinerary(day=day_data["day"], activities=activities))

        return ItineraryResponse(itinerary=itinerary)

    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)