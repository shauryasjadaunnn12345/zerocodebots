from django.shortcuts import render


def home(request):
    from .models import Blog
    blogs = Blog.objects.filter(is_published=True)[:6]
    return render(request, 'home.html', {'blogs': blogs})


from django.conf import settings
# Create your views here.
# projects/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, QuestionAnswer, Lead, AnalyticsEvent, Feedback, ConversationContext, BotResponse, Blog
from .forms import ProjectForm, QuestionAnswerForm, BlogForm
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from urllib.parse import urlparse
def features(request):
    return render(request,"features.html")

def about(request):
    return render(request,"about.html")

def contact(request):
    return render(request,"contactus.html")

def services(request):
    return render(request,"services.html")
@login_required
def create_project_view(request):
    # Check if user already has a project
    existing_project = Project.objects.filter(user=request.user).first()

    # If project exists, redirect to the edit page
    if existing_project:
        return redirect('edit_project', pk=existing_project.pk)

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user  # Ensure project belongs to logged-in user
            project.save()
            return redirect('edit_project', pk=project.pk)
    else:
        form = ProjectForm()

    return render(request, 'create_project.html', {
        'form': form
    })


from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import traceback

@login_required
def edit_project_view(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)

    QAFormSet = modelformset_factory(
        QuestionAnswer,
        form=QuestionAnswerForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        try:
            formset = QAFormSet(
                request.POST,
                request.FILES,
                queryset=project.qas.all()
            )

            if formset.is_valid():
                instances = formset.save(commit=False)

                for instance in instances:
                    instance.project = project
                    instance.save()

                for obj in formset.deleted_objects:
                    obj.delete()

                messages.success(request, "Project updated successfully")
                return redirect('edit_project', pk=pk)
            else:
                print("❌ FORMSET ERRORS:", formset.errors)

        except Exception as e:
            print("❌ EDIT PROJECT CRASH:", str(e))
            traceback.print_exc()
            messages.error(request, "Something went wrong while saving.")

    else:
        formset = QAFormSet(queryset=project.qas.all())

    return render(request, 'edit_project.html', {
    'project': project,
    'formset': formset,
})



@login_required
@require_POST
def import_from_website(request, pk):
    """Fetch a website URL and generate basic Q/A pairs into the project.

    Strategy:
    - Fetch HTML with `requests`.
    - Parse headings (h1-h3) and following paragraph text using BeautifulSoup
      when available, otherwise perform a simple fallback extraction.
    - Create up to 20 `QuestionAnswer` entries that do not already exist.
    """
    project = get_object_or_404(Project, pk=pk, user=request.user)
    url = (request.POST.get('website_url') or '').strip()
    if not url:
        return JsonResponse({'error': 'Missing website_url'}, status=400)

    # Basic server-side URL validation
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return JsonResponse({'error': 'Invalid URL (must be http/https).'}, status=400)

    try:
        resp = requests.get(url, timeout=10)
        # limit fetched size to avoid huge downloads
        content = resp.text or ''
        html = content[:200000]
    except Exception as e:
        return JsonResponse({'error': f'Failed to fetch URL: {e}'}, status=400)

    qas = []
    # Always use AI generation to produce Q/A pairs from page text.
    use_ai = True

    if use_ai:
        try:
            # prepare a concise prompt asking for JSON array of {question,answer}
            prompt = (
                "You are given the text content of a web page. Extract up to 20 concise, "
                "useful question and answer pairs that a user might ask about the page. "
                "Return ONLY a JSON array of objects with keys 'question' and 'answer'. "
                "Example: [{\"question\": \"What is X?\", \"answer\": \"X is...\"}, ...].\n\n"
                "Page content:\n" + html[:10000]
            )

            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_KEY}",
                "Referer": "https://zerocodebots.onrender.com/",
                "X-Title": "Project Chatbot",
                "Content-Type": "application/json",
            }
            data = {
                "model": "google/gemma-3-12b-it:free",
                "messages": [{"role": "user", "content": prompt}],
            }
            try:
                openr = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                openr.raise_for_status()
                resp_json = openr.json()
                content_text = resp_json.get('choices', [])[0].get('message', {}).get('content', '')
            except Exception:
                content_text = ''

            if content_text:
                # strip possible ```json fences
                cand = content_text.strip()
                if cand.startswith('```'):
                    parts = cand.split('```')
                    if len(parts) >= 3:
                        inner = parts[1]
                        if '\n' in inner:
                            inner = inner.split('\n', 1)[1]
                        cand = inner.strip()

                try:
                    import json as _json
                    parsed_json = _json.loads(cand)
                    if isinstance(parsed_json, list):
                        for item in parsed_json:
                            if not isinstance(item, dict):
                                continue
                            q = (item.get('question') or '').strip()
                            a = (item.get('answer') or '').strip()
                            if q and a:
                                qas.append((q, a))
                except Exception:
                    # fall back to non-AI extraction below
                    qas = []
        except Exception:
            qas = []
    # If AI didn't produce pairs, prefer BeautifulSoup extraction
    try:
        from bs4 import BeautifulSoup  # type: ignore
        soup = BeautifulSoup(html, 'html.parser')
        # collect headings and their next paragraph siblings
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            q_text = tag.get_text(strip=True)
            # find the next paragraph or sibling text
            ans_text = ''
            next_p = tag.find_next(lambda t: t.name == 'p' and t.get_text(strip=True))
            if next_p:
                ans_text = next_p.get_text(separator=' ', strip=True)
            else:
                # fallback: gather following sibling text nodes
                sib_texts = []
                for sib in tag.next_siblings:
                    if getattr(sib, 'name', None) and sib.name.startswith('h'):
                        break
                    txt = getattr(sib, 'get_text', lambda **kw: '')(separator=' ', strip=True)
                    if txt:
                        sib_texts.append(txt)
                    if len(sib_texts) >= 2:
                        break
                ans_text = ' '.join(sib_texts).strip()

            if q_text and ans_text:
                qas.append((q_text, ans_text))
            if len(qas) >= 40:
                break
    except Exception:
        # Simple regex fallback: extract <h1>-<h3> and next <p>
        import re
        headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html, flags=re.I | re.S)
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, flags=re.I | re.S)
        # Pair them naively
        for i, h in enumerate(headings[:40]):
            a = paragraphs[i] if i < len(paragraphs) else ''
            q = re.sub(r'<[^>]+>', '', h).strip()
            a = re.sub(r'<[^>]+>', '', a).strip()
            if q and a:
                qas.append((q, a))

    created = 0
    skipped = 0
    created_items = []
    for q_text, a_text in qas:
        if created >= 20:
            break
        try:
            q_short = q_text[:255]
            exists = project.qas.filter(question__iexact=q_short).exists()
            if exists:
                skipped += 1
                continue
            qa = QuestionAnswer.objects.create(project=project, question=q_short, answer=a_text)
            created += 1
            created_items.append({'id': qa.id, 'question': qa.question})
        except Exception:
            continue

    return JsonResponse({'created': created, 'skipped': skipped, 'items': created_items})

@login_required
def dashboard(request):
    return render(request,"dashboard.html")
# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from .forms import *
from .models import OTPVerification

from django.contrib import messages
from django.utils import timezone
from .forms import SignupForm, OTPForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .models import OTPVerification

# 🔹 Signup
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from .forms import SignupForm
from .models import OTPVerification


def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            # Set password properly
            user.set_password(form.cleaned_data["password"])
            user.is_active = False
            user.save()

            # OTP handling
            otp_obj, _ = OTPVerification.objects.get_or_create(user=user)
            otp_obj.generate_otp()

            send_mail(
    subject="Your ZeroCodeBots OTP Verification Code",
    message=(
        f"Hi {user.username},\n\n"
        f"Your One-Time Password (OTP) for verifying your request is:\n\n"
        f"🔐 {otp_obj.otp}\n\n"
        f"This OTP is valid for a limited time. Please do not share it with anyone.\n\n"
        f"If you did not request this code, you can safely ignore this email.\n\n"
        f"Thanks,\n"
        f"ZeroCodeBots Security Team"
    ),
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[user.email],
    fail_silently=False,
)


            request.session["uid"] = user.id
            return redirect("verify_otp")

    else:
        form = SignupForm()

    return render(request, "signup.html", {"form": form})

# 🔹 Verify OTP
def verify_otp_view(request):
    uid = request.session.get('uid')
    user = get_object_or_404(User, id=uid)
    otp_obj = get_object_or_404(OTPVerification, user=user)

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['otp'] == otp_obj.otp:
                user.is_active = True
                user.save()
                # remove OTP record
                otp_obj.delete()
                # Log the user in immediately so they don't need to re-enter credentials
                from django.contrib.auth import login

                login(
                request,
                 user,
                 backend="django.contrib.auth.backends.ModelBackend",
                 )

                messages.success(request, "Account verified and logged in!")
                return redirect('dashboard')
            else:
                form.add_error('otp', 'Invalid OTP')
    else:
        form = OTPForm()
    return render(request, 'verify_otp.html', {'form': form})


# 🔹 Login
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('home')  # or dashboard
            else:
                form.add_error(None, 'Invalid credentials')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


# 🔹 Logout
def logout_view(request):
    logout(request)
    return redirect('login')


# 🔹 Forgot Password
def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                otp_obj, _ = OTPVerification.objects.get_or_create(user=user)
                otp_obj.generate_otp()

                send_mail(
                    "Reset OTP Code",
                    f"Your OTP is: {otp_obj.otp}",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False
                )

                request.session['uid'] = user.id
                return redirect('reset_otp')
            except User.DoesNotExist:
                form.add_error('email', 'Email not found')
    else:
        form = ForgotPasswordForm()
    return render(request, 'forgot_password.html', {'form': form})


# 🔹 Reset OTP
def reset_otp_view(request):
    uid = request.session.get('uid')
    user = get_object_or_404(User, id=uid)
    otp_obj = get_object_or_404(OTPVerification, user=user)

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['otp'] == otp_obj.otp:
                return redirect('reset_password')
            else:
                form.add_error('otp', 'Invalid OTP')
    else:
        form = OTPForm()
    return render(request, 'reset_otp.html', {'form': form})


# 🔹 Resend OTP (for reset flow)
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

def resend_otp_view(request):
    uid = request.session.get("uid")
    user = get_object_or_404(User, id=uid)

    otp_obj, _ = OTPVerification.objects.get_or_create(user=user)
    otp_obj.generate_otp()

    subject = "Your ZeroCodeBots Password Reset OTP"

    message = f"""
Hello {user.username},

We received a request to reset your ZeroCodeBots account password.

Your One-Time Password (OTP) is:

{otp_obj.otp}

This OTP is valid for a short time. Please do not share it with anyone.

If you did not request this password reset, you can safely ignore this email.

Best regards,
ZeroCodeBots Team
"""

    send_mail(
        subject=subject,
        message=message.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("reset_otp")


# 🔹 Reset Password
def reset_password_view(request):
    uid = request.session.get('uid')
    user = get_object_or_404(User, id=uid)

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            OTPVerification.objects.filter(user=user).delete()
            messages.success(request, "Password reset successful.")
            return redirect('login')
    else:
        form = ResetPasswordForm()
    return render(request, 'reset_password.html', {'form': form})
@login_required
def my_projects_view(request):
    projects = Project.objects.filter(user=request.user)
    return render(request, 'my_projects.html', {'projects': projects})


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from django.utils.dateparse import parse_date
import json

from .ai.agent import generate_openrouter_answer
from .ai.i18n import detect_language
import difflib
from django.http import HttpResponse
from .analytics_utils import export_project_csv
from .analytics_utils import aggregate_project, time_series_events, top_questions, intent_breakdown, recent_events


def _track_event(project, event_type, metadata=None):
    """
    Lightweight analytics tracker. Never breaks the main flow.
    """
    try:
        AnalyticsEvent.objects.create(
            project=project,
            event_type=event_type,
            metadata=metadata or {},
        )
    except Exception as e:
        # Avoid crashing the request on analytics failures
        print(f"WARN: failed to track analytics event '{event_type}': {e}")


def _handle_intent(project, ai_payload):
    """
    Handle the structured intent coming from the AI layer.

    - answer   → just return the message
    - lead     → save a lead (best-effort) and return the message
    - booking  → placeholder handler (no-op for now, just echo)
    - greeting → simple greeting/intro, treated like an answer
    - unknown  → fallback-safe response
    """
    intent = ai_payload.get("intent", "unknown")
    message = ai_payload.get("message", "")
    data = ai_payload.get("data", {}) or {}

    # Respect per-project allowed intents. If the detected intent is
    # not enabled for this project, downgrade it to "unknown" so that
    # existing flows (fallback, analytics, etc.) handle it safely.
    allowed = project.allowed_intents or ["answer", "lead", "booking", "greeting", "unknown"]
    if intent not in allowed:
        intent = "unknown"

    # Track detected intent
    _track_event(
        project,
        "intent_detected",
        {
            "intent": intent,
        },
    )

    # Ensure data is a dict
    if not isinstance(data, dict):
        data = {}

    if intent == "lead":
        # Best-effort extraction of lead details from data
        name = data.get("name") or data.get("full_name") or ""
        email = data.get("email") or ""

        try:
            lead = Lead.objects.create(
                project=project,
                name=name[:255] if isinstance(name, str) else "",
                email=email if isinstance(email, str) else "",
            )
            _track_event(
                project,
                "lead_created",
                {
                    "lead_id": lead.id,
                    "name": lead.name,
                    "email": lead.email,
                },
            )
        except Exception as e:
            # Do not break chat flow on DB issues
            print("WARN: failed to save lead:", str(e))

        # You can enrich data with a flag that a lead was created
        data.setdefault("lead_saved", True)

    elif intent == "booking":
        # Placeholder booking handler – extend later
        data.setdefault("booking_handled", False)

    elif intent == "unknown":
        # Ensure a friendly fallback message
        if not message:
            message = "I'm not sure how to handle that yet, but your message was received."

        _track_event(
            project,
            "fallback_triggered",
            {
                "reason": "unknown_intent",
            },
        )

    # For "answer" (and others) we just pass through
    return {
        "intent": intent,
        "message": message,
        "data": data,
    }
@csrf_exempt
def ask_bot(request, project_id):
    if request.method == 'POST':
        try:
            question = request.POST.get('question')
            project = get_object_or_404(Project, pk=project_id)

            # Detect and persist user language (English/Hindi for now)
            previous_lang = request.session.get("chat_lang", "en")
            language_code = detect_language(question, default=previous_lang)
            request.session["chat_lang"] = language_code

            # Track that a user message was sent
            _track_event(
                project,
                "message_sent",
                {
                    "question": question,
                    "language": language_code,
                },
            )

            ai_payload = generate_openrouter_answer(project, question, language_code=language_code)
            handled = _handle_intent(project, ai_payload)

            # Confidence extraction (AI may include top-level or in data)
            def _extract_confidence(payload):
                c = None
                if not payload:
                    return None
                if isinstance(payload, dict):
                    c = payload.get('confidence')
                    if c is None:
                        data = payload.get('data') or {}
                        c = data.get('confidence')
                try:
                    if c is not None:
                        return float(c)
                except Exception:
                    return None
                return None

            confidence = _extract_confidence(ai_payload)

            # Persist response for analytics / tuning
            bot_resp = None
            try:
                bot_resp = BotResponse.objects.create(
                    project=project,
                    question=question or "",
                    response=handled.get('message', ''),
                    confidence=confidence,
                    payload=ai_payload,
                )
            except Exception as e:
                print('WARN: failed to save BotResponse:', e)

            # Optional: persist context memory items if returned by the model
            try:
                data = ai_payload.get('data') or {}
                memory = data.get('context_memory') or data.get('memory')
                if isinstance(memory, dict):
                    session_key = request.session.session_key or ''
                    for k, v in memory.items():
                        try:
                            ConversationContext.objects.create(
                                project=project,
                                session_key=session_key,
                                key=str(k),
                                value=v,
                            )
                        except Exception as e:
                            print('WARN: failed to save context:', e)
            except Exception as e:
                print('WARN: memory extraction error:', e)

            # Track available structured features: MCQ, clarification, confidence
            structured = {}
            try:
                data = ai_payload.get('data') or {}
                if 'mcq' in ai_payload:
                    structured['mcq'] = ai_payload.get('mcq')
                if 'mcq' in data:
                    structured['mcq'] = data.get('mcq')
                if 'clarify' in ai_payload:
                    structured['clarify'] = ai_payload.get('clarify')
                if 'clarify' in data:
                    structured['clarify'] = data.get('clarify')
                if confidence is not None:
                    structured['confidence'] = confidence
            except Exception:
                structured = {}

            if structured.get('mcq'):
                _track_event(project, 'mcq_present', {'mcq_count': len(structured.get('mcq') or [])})

            # Keep existing flow: "answer" is still the main text response
            # while also exposing structured intent and data.
            resp = {
                'answer': handled.get('message', ''),
                'intent': handled.get('intent', 'unknown'),
                'data': handled.get('data', {}),
            }
            if bot_resp is not None:
                resp['bot_response_id'] = bot_resp.id
            # merge structured items into response under top-level keys
            resp.update(structured)

            # If the AI didn't include an image but a matching QuestionAnswer has one,
            # attach it to the response so the frontend can render images stored in the QA.
            try:
                # If model returned an image inside `data`, prefer/promote it to
                # a top-level `image` field (normalizing to an absolute URL when
                # possible) so existing frontends can render it uniformly.
                model_image = None
                try:
                    model_image = (ai_payload.get('data') or {}).get('image')
                except Exception:
                    model_image = None

                if model_image and isinstance(model_image, dict):
                    img_url = model_image.get('url') or ''
                    img_desc = model_image.get('caption') or model_image.get('description') or model_image.get('reason') or ''
                    try:
                        if img_url and not img_url.startswith('http'):
                            img_url = request.build_absolute_uri(img_url)
                    except Exception:
                        pass

                    if img_url or img_desc:
                        resp['image'] = {'url': img_url, 'description': img_desc}

                # Only run QA-based attachment when no image is present yet.
                if 'image' not in resp or not resp.get('image'):
                    qa_match = None
                    if question:
                        # Exact match first
                        qa_match = project.qas.filter(question__iexact=question).first()
                    # Fallback: contains
                    if not qa_match and question:
                        qa_match = project.qas.filter(question__icontains=question).first()

                    # If still no match, try fuzzy similarity against QAs that have images
                    if not qa_match and question:
                        try:
                            best = None
                            best_score = 0.0
                            q_lower = question.lower().strip()
                            handled_msg = (handled.get('message') or '').lower().strip()

                            def token_overlap(a: str, b: str) -> float:
                                sa = set(a.split())
                                sb = set(b.split())
                                if not sa or not sb:
                                    return 0.0
                                inter = sa.intersection(sb)
                                return len(inter) / max(1, min(len(sa), len(sb)))

                            for qa in project.qas.all():
                                if not getattr(qa, 'image'):
                                    continue
                                qa_q = (qa.question or '').lower().strip()
                                if not qa_q:
                                    continue

                                # similarity against user question and AI message
                                score_q = difflib.SequenceMatcher(None, q_lower, qa_q).ratio() if q_lower else 0.0
                                score_msg = difflib.SequenceMatcher(None, handled_msg, qa_q).ratio() if handled_msg else 0.0
                                # token overlap as alternative signal
                                overlap_q = token_overlap(q_lower, qa_q) if q_lower else 0.0
                                overlap_msg = token_overlap(handled_msg, qa_q) if handled_msg else 0.0

                                score = max(score_q, score_msg, overlap_q, overlap_msg)
                                if score > best_score:
                                    best_score = score
                                    best = qa

                            # threshold: accept only reasonably similar matches
                            if best and best_score >= 0.45:
                                qa_match = best
                                try:
                                    _track_event(project, 'qa_image_matched', {'qa_id': qa_match.id, 'score': best_score})
                                except Exception:
                                    pass
                        except Exception:
                            qa_match = None

                    if qa_match and getattr(qa_match, 'image'):
                        try:
                            image_url = request.build_absolute_uri(qa_match.image.url)
                        except Exception:
                            image_url = qa_match.image.url if qa_match.image else ''

                        resp['image'] = {
                            'url': image_url,
                            'description': qa_match.image_description or ''
                        }

                        # Persist into BotResponse.payload for analytics / later inspection
                        if bot_resp is not None:
                            try:
                                payload = bot_resp.payload or {}
                                payload['qa_image'] = {
                                    'qa_id': qa_match.id,
                                    'url': resp['image']['url'],
                                    'description': resp['image']['description'],
                                }
                                bot_resp.payload = payload
                                bot_resp.save(update_fields=['payload'])
                            except Exception as e:
                                print('WARN: failed to update BotResponse payload with QA image:', e)
            except Exception as e:
                print('WARN: failed to attach QA image:', e)

            return JsonResponse(resp)
        except Exception as e:
            import traceback
            print("ERROR in ask_bot:", str(e))
            traceback.print_exc()
            return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
def debug_qa_match(request, pk):
    """Debug endpoint: return best QA match for input question `q` (and optional `msg`).

    GET params:
      - q: user question text
      - msg: AI-handled message (optional)

    Only accessible to the project owner.
    """
    project = get_object_or_404(Project, pk=pk, user=request.user)
    q = (request.GET.get('q') or '').strip()
    msg = (request.GET.get('msg') or '').strip()

    if not q and not msg:
        return JsonResponse({'error': 'Provide q or msg as query parameter'}, status=400)

    q_lower = q.lower()
    msg_lower = msg.lower()

    # 1) exact
    qa_match = None
    if q:
        qa_match = project.qas.filter(question__iexact=q).first()
    # 2) contains
    if not qa_match and q:
        qa_match = project.qas.filter(question__icontains=q).first()

    # 3) fuzzy candidates (score from multiple signals)
    best = None
    best_score = 0.0
    second = None
    second_score = 0.0

    def token_overlap(a: str, b: str) -> float:
        sa = set(a.split())
        sb = set(b.split())
        if not sa or not sb:
            return 0.0
        inter = sa.intersection(sb)
        return len(inter) / max(1, min(len(sa), len(sb)))

    try:
        for qa in project.qas.all():
            qa_q = (qa.question or '').lower().strip()
            if not qa_q:
                continue
            score_q = difflib.SequenceMatcher(None, q_lower, qa_q).ratio() if q_lower else 0.0
            score_msg = difflib.SequenceMatcher(None, msg_lower, qa_q).ratio() if msg_lower else 0.0
            overlap_q = token_overlap(q_lower, qa_q) if q_lower else 0.0
            overlap_msg = token_overlap(msg_lower, qa_q) if msg_lower else 0.0
            score = max(score_q, score_msg, overlap_q, overlap_msg)
            if score > best_score:
                second, second_score = best, best_score
                best, best_score = qa, score
            elif score > second_score:
                second, second_score = qa, score
    except Exception as e:
        print('WARN debug match loop failed', e)

    # prefer earlier exact/contains match if present and has image
    if qa_match and getattr(qa_match, 'image', None):
        chosen = qa_match
        chosen_score = 1.0
    else:
        chosen = best
        chosen_score = best_score

    result = {
        'provided_q': q,
        'provided_msg': msg,
        'chosen': None,
        'chosen_score': None,
        'second': None,
        'second_score': None,
    }

    if chosen:
        img_url = ''
        img_desc = ''
        try:
            if getattr(chosen, 'image', None):
                img_url = request.build_absolute_uri(chosen.image.url)
                img_desc = chosen.image_description or ''
        except Exception:
            img_url = getattr(chosen, 'image', None) and getattr(chosen.image, 'url', '')

        result['chosen'] = {'id': chosen.id, 'question': chosen.question, 'has_image': bool(getattr(chosen, 'image', None)), 'image_url': img_url, 'image_description': img_desc}
        result['chosen_score'] = float(chosen_score or 0.0)

    if second:
        result['second'] = {'id': second.id, 'question': second.question}
        result['second_score'] = float(second_score or 0.0)

    return JsonResponse(result)


@csrf_exempt
def submit_feedback(request, project_id):
    """Accepts POST feedback: rating, comment, selected_option, question, response"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        project = get_object_or_404(Project, pk=project_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        selected = request.POST.get('selected_option', '')
        question = request.POST.get('question', '')
        response_text = request.POST.get('response', '')

        bot_resp = None
        brid = request.POST.get('bot_response_id')
        if brid:
            try:
                bot_resp = BotResponse.objects.filter(project=project, id=int(brid)).first()
            except Exception:
                bot_resp = None

        fb = Feedback.objects.create(
            project=project,
            question=question,
            response=response_text,
            rating=int(rating) if rating else None,
            comment=comment,
            selected_option=selected or None,
            bot_response=bot_resp,
        )

        _track_event(project, 'feedback_submitted', {
            'feedback_id': fb.id,
            'rating': fb.rating,
            'selected_option': fb.selected_option,
        })

        return JsonResponse({'ok': True, 'feedback_id': fb.id})
    except Exception as e:
        print('ERROR submit_feedback:', e)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
def project_analytics(request, pk):
    """Return a concise analytics summary for the project (counts by event type)."""
    project = get_object_or_404(Project, pk=pk, user=request.user)
    # Basic summary: counts of AnalyticsEvent and average confidence
    events = AnalyticsEvent.objects.filter(project=project).values('event_type')
    summary = {}
    for row in events:
        et = row['event_type']
        summary.setdefault(et, 0)
        summary[et] += 1

    # Average confidence from saved responses
    responses = BotResponse.objects.filter(project=project).exclude(confidence__isnull=True)
    avg_conf = None
    try:
        if responses.exists():
            avg_conf = float(responses.aggregate(Avg('confidence'))['confidence__avg'])
    except Exception:
        avg_conf = None

    return JsonResponse({
        'event_counts': summary,
        'responses_count': BotResponse.objects.filter(project=project).count(),
        'avg_confidence': avg_conf,
    })


@login_required
def export_analytics(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    csv_text = export_project_csv(project)
    resp = HttpResponse(csv_text, content_type='text/csv')
    resp['Content-Disposition'] = f'attachment; filename="project_{project.id}_analytics.csv"'
    return resp


@login_required
def project_analytics_dashboard(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)

    # parse optional filters: start, end, intent
    start = request.GET.get('start')
    end = request.GET.get('end')
    intent = request.GET.get('intent')
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    summary = aggregate_project(project)
    timeseries = time_series_events(project, start_date=start_date, end_date=end_date, intent=intent)
    top_qs = top_questions(project, limit=10, start_date=start_date, end_date=end_date, intent=intent)
    intents = intent_breakdown(project, start_date=start_date, end_date=end_date)

    # prepare JSON for charting and downsample if too many points
    chart_labels = [t['date'] for t in timeseries]
    chart_values = [t['count'] for t in timeseries]

    # Downsample to at most `max_points` for performance (simple bucket aggregation)
    max_points = 60
    if len(chart_values) > max_points and len(chart_values) > 0:
        from math import ceil
        bucket_size = ceil(len(chart_values) / max_points)
        ds_labels = []
        ds_values = []
        for i in range(0, len(chart_values), bucket_size):
            chunk_vals = chart_values[i:i+bucket_size]
            chunk_labels = chart_labels[i:i+bucket_size]
            total = sum(chunk_vals)
            # label as range when bucket contains multiple days
            if len(chunk_labels) > 1:
                lbl = f"{chunk_labels[0]} - {chunk_labels[-1]}"
            else:
                lbl = chunk_labels[0]
            ds_labels.append(lbl)
            ds_values.append(total)
        chart_labels, chart_values = ds_labels, ds_values

    return render(request, 'project_analytics_dashboard.html', {
        'project': project,
        'summary': summary,
        'timeseries': timeseries,
        'top_questions': top_qs,
        'intent_breakdown': intents,
        'recent_logs': recent_events(project, limit=50, start_date=start_date, end_date=end_date, intent=intent),
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
        'filter_start': start,
        'filter_end': end,
        'filter_intent': intent,
    })



@login_required
def chatbot_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id, user=request.user)
    chat_lang = request.session.get('chat_lang', 'en')
    return render(request, 'chatbot.html', {'project': project, 'chat_lang': chat_lang})
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from home.models import Project

def embed_chatbot(request):
    bot_key = request.GET.get('key')
    if not bot_key:
        raise Http404("Missing 'key' parameter in URL")

    project = get_object_or_404(Project, bot_key=bot_key)
    chat_lang = request.session.get('chat_lang', 'en')
    return render(request, 'embed_chatbot.html', {'project': project, 'chat_lang': chat_lang})

@login_required
def project_summary_view(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    return render(request, 'project_summary.html', {'project': project})
from django.shortcuts import render
from django.http import HttpResponse

def robots_txt(request):
    return render(request, 'robots.txt', content_type='text/plain')

def sitemap_xml(request):
    return render(request, 'sitemap.xml', content_type='application/xml')


# Blog Views
def blog_list(request):
    """Display all published blogs with pagination"""
    from django.core.paginator import Paginator
    from django.utils.text import slugify
    
    category = request.GET.get('category')
    search = request.GET.get('search', '')
    
    blogs = Blog.objects.filter(is_published=True)
    
    if category and category != 'all':
        blogs = blogs.filter(category=category)
    
    if search:
        blogs = blogs.filter(title__icontains=search) | blogs.filter(content__icontains=search)
    
    paginator = Paginator(blogs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = [cat[0] for cat in Blog._meta.get_field('category').choices]
    
    return render(request, 'blog_list.html', {
        'page_obj': page_obj,
        'blogs': page_obj.object_list,
        'categories': categories,
        'selected_category': category,
        'search_query': search
    })


from django.shortcuts import render, get_object_or_404
from .models import Blog


from django.shortcuts import render, get_object_or_404
from .models import Blog

from django.views.decorators.cache import cache_page

from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from .models import Blog


@cache_page(60 * 5)  # 5 minutes
def blog_detail(request, slug):
    """
    Cached blog detail view.
    NO database mutations allowed here.
    """

    blog = get_object_or_404(
        Blog.objects.select_related("author"),
        slug=slug,
        is_published=True
    )

    related_blogs = (
        Blog.objects
        .filter(category=blog.category, is_published=True)
        .exclude(pk=blog.pk)
        .only("id", "title", "slug", "excerpt", "featured_image")[:3]
    )

    def get_image_base(obj):
        if not obj.featured_image:
            return ""
        url = obj.featured_image.url
        directory, filename = url.rsplit("/", 1)
        return f"{directory}/{filename.rsplit('.', 1)[0]}"

    blog.featured_image_base = get_image_base(blog)
    for r in related_blogs:
        r.featured_image_base = get_image_base(r)

    return render(
        request,
        "blog_detail.html",
        {
            "blog": blog,
            "related_blogs": related_blogs,
        },
    )

@login_required
def create_blog(request):
    """Create a new blog post"""
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user
            from django.utils.text import slugify
            blog.slug = slugify(blog.title)
            blog.save()
            messages.success(request, 'Blog created successfully!')
            return redirect('blog_detail', slug=blog.slug)
    else:
        form = BlogForm()
    
    return render(request, 'create_blog.html', {'form': form})


@login_required
def edit_blog(request, pk):
    """Edit an existing blog post"""
    blog = get_object_or_404(Blog, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            blog = form.save(commit=False)
            from django.utils.text import slugify
            blog.slug = slugify(blog.title)
            blog.save()
            messages.success(request, 'Blog updated successfully!')
            return redirect('blog_detail', slug=blog.slug)
    else:
        form = BlogForm(instance=blog)
    
    return render(request, 'edit_blog.html', {'form': form, 'blog': blog})


@login_required
def delete_blog(request, pk):
    """Delete a blog post"""
    blog = get_object_or_404(Blog, pk=pk, author=request.user)
    
    if request.method == 'POST':
        blog.delete()
        messages.success(request, 'Blog deleted successfully!')
        return redirect('my_blogs')
    
    return render(request, 'delete_blog.html', {'blog': blog})

from django.contrib.auth.decorators import login_required
from django.db.models import Sum

@login_required
def my_blogs(request):
    blogs = Blog.objects.filter(author=request.user)

    total_blogs = blogs.count()
    published_count = blogs.filter(is_published=True).count()
    total_views = blogs.aggregate(total=Sum('views'))['total'] or 0

    context = {
        'blogs': blogs,
        'total_blogs': total_blogs,
        'published_count': published_count,
        'total_views': total_views,
    }

    return render(request, 'my_blogs.html', context)

@login_required
def my_projects(request):
    """Display user's projects"""
    project = Project.objects.filter(user=request.user).first()
    
    if not project:
        return redirect('create_project')
    
    return render(request, 'my_projects.html', {'project': project})
from home.breadcrumbs import get_breadcrumbs

def dashboard(request):
    context = {
        "breadcrumbs": get_breadcrumbs(request)
    }
    return render(request, "dashboard.html", context)

# Newsletter Views
@require_POST
def subscribe_newsletter(request):
    """
    API endpoint to handle newsletter subscription.
    Accepts email via POST request and stores in Newsletter model.
    Returns JSON response with success/error message.
    """
    import json
    from django.core.mail import send_mail
    from .models import Newsletter
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        # Validate email
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'}, status=400)
        
        # Check if email already exists
        if Newsletter.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'This email is already subscribed.'}, status=400)
        
        # Create newsletter subscriber
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        newsletter = Newsletter.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Optional: Send confirmation email
        try:
            send_mail(
                subject='Welcome to ZeroCodeBots Newsletter!',
                message=f'''Hello,

Thank you for subscribing to the ZeroCodeBots newsletter!

You'll now receive updates about:
- New features and product releases
- No-code automation tips and best practices
- Success stories from our community
- Special offers and promotions

If you have any questions, feel free to reach out to us at contact@zerocodebots.com

Best regards,
The ZeroCodeBots Team

---
ZeroCodeBots
Empowering everyone to build powerful automation tools without writing code.
https://zerocodebots.com
''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True
            )
        except:
            pass  # Email sending is optional
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully subscribed to the newsletter!'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)


def get_client_ip(request):
    """
    Get client IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
def privacy_policy(request):
    return render(request, 'privacy_policy.html')
def terms_of_service(request):

    return render(request, 'terms_of_service.html')

