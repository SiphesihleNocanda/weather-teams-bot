"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import os

from dotenv import load_dotenv

load_dotenv()

dotenv_path = os.path.join(os.path.dirname(__file__), "..", "env", ".env.local.user")
load_dotenv(dotenv_path, override=True)

class Config:
    """Bot Configuration"""

    PORT = 3978
    APP_ID = os.environ.get("BOT_ID", "")
    APP_PASSWORD = os.environ.get("BOT_PASSWORD", "")
    APP_TYPE = os.environ.get("BOT_TYPE", "")
    APP_TENANTID = os.environ.get("BOT_TENANT_ID", "")
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"] # OpenAI API key
    OPENAI_ASSISTANT_ID = os.environ["OPENAI_ASSISTANT_ID"] # OpenAI Assistant ID
    OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API_KEY"]
    API_NINJAS_API_KEY = os.environ["API_NINJAS_API_KEY"]