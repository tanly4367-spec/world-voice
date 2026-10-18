# World Voice

Translate typed text, hear the translation, and view pronunciation guides where available. Includes eight page languages and a responsive phone layout.

## Free Render hosting

Create a Render Web Service from this repository. Choose Python, build command `pip install -r requirements.txt`, start command `python app.py --local`, and the **Free** instance. Set `PYTHON_VERSION` to `3.12.10`. No database or paid hardware is required.

The stable onrender.com address stays the same through restarts. Free services can sleep after inactivity and take a moment to restart. Translation and speech depend on external Google web services; availability and accuracy are not guaranteed.

## Local run

    pip install -r requirements.txt
    python app.py --local

Submitted translation and speech text is processed by Google. Do not enter sensitive information. The optional portrait is loaded from a Facebook-hosted image URL and may expire.
