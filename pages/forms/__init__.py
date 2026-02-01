# __init__.py
# This file makes the forms directory a Python package
from .form_drug_testing import FormDrugTesting
from .form_vitamin_b import FormVitaminB
from .form_certificate_fitness import FormCertificateFitness
from .form_heights_questionnaire import FormHeightsQuestionnaire
from .form_hot_cold_exposure import FormHotColdExposure
from .form_confined_spaces import FormConfinedSpaces
from .form_musculoskeletal import FormMusculoskeletal
from .form_psychology import FormPsychology
from .form_cwb_referral import FormCWBReferral
from .form_complete_wellbeing import FormCompleteWellbeing
from .form_annexure3 import FormAnnexure3

__all__ = [
    'FormDrugTesting',
    'FormVitaminB',
    'FormCertificateFitness',
    'FormHeightsQuestionnaire',
    'FormHotColdExposure',
    'FormConfinedSpaces',
    'FormMusculoskeletal',
    'FormPsychology',
    'FormCWBReferral',
    'FormCompleteWellbeing',
    'FormAnnexure3'
]
