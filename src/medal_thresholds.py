"""Medal score thresholds for MLE-bench competitions.

Pre-computed from leaderboard.csv files using the same position-based
logic as mlebench/grade_helpers.py (Kaggle medal rules). The agent
receives only the threshold values — no leaderboard data, no online
access required.

Usage:
    from src.medal_thresholds import get_medal_thresholds
    info = get_medal_thresholds("spaceship-titanic")
    # {"gold": 0.82066, "silver": 0.81388, "bronze": 0.80967,
    #  "median": 0.79565, "is_lower_better": False}
"""

from __future__ import annotations

# 82 competitions — extracted from mlebench/competitions/*/leaderboard.csv
MEDAL_THRESHOLDS: dict[str, dict] = {
    "3d-object-detection-for-autonomous-vehicles": {"gold": 0.139, "silver": 0.053, "bronze": 0.046, "median": 0.042, "is_lower_better": False},
    "AI4Code": {"gold": 0.9006, "silver": 0.8598, "bronze": 0.8534, "median": 0.8257, "is_lower_better": False},
    "aerial-cactus-identification": {"gold": 1.0, "silver": 1.0, "bronze": 1.0, "median": 0.9991, "is_lower_better": False},
    "alaska2-image-steganalysis": {"gold": 0.928, "silver": 0.921, "bronze": 0.915, "median": 0.904, "is_lower_better": False},
    "aptos2019-blindness-detection": {"gold": 0.93051, "silver": 0.91965, "bronze": 0.91449, "median": 0.88891, "is_lower_better": False},
    "billion-word-imputation": {"gold": 5.37017, "silver": 5.54372, "bronze": 5.55209, "median": 5.55211, "is_lower_better": True},
    "bms-molecular-translation": {"gold": 0.62, "silver": 1.37, "bronze": 1.99, "median": 5.58, "is_lower_better": True},
    "cassava-leaf-disease-classification": {"gold": 0.9013, "silver": 0.8992, "bronze": 0.8978, "median": 0.8909, "is_lower_better": False},
    "cdiscount-image-classification-challenge": {"gold": 0.77604, "silver": 0.73526, "bronze": 0.70898, "median": 0.44055, "is_lower_better": False},
    "chaii-hindi-and-tamil-question-answering": {"gold": 0.76305, "silver": 0.73984, "bronze": 0.73725, "median": 0.72756, "is_lower_better": False},
    "champs-scalar-coupling": {"gold": -2.87509, "silver": -2.03119, "bronze": -1.90122, "median": -0.9529, "is_lower_better": True},
    "denoising-dirty-documents": {"gold": 0.01794, "silver": 0.02609, "bronze": 0.04517, "median": 0.07325, "is_lower_better": True},
    "detecting-insults-in-social-commentary": {"gold": 0.83321, "silver": 0.82307, "bronze": 0.79111, "median": 0.77842, "is_lower_better": False},
    "dog-breed-identification": {"gold": 0.0005, "silver": 0.00539, "bronze": 0.04598, "median": 0.47205, "is_lower_better": True},
    "dogs-vs-cats-redux-kernels-edition": {"gold": 0.03882, "silver": 0.05038, "bronze": 0.06127, "median": 0.12216, "is_lower_better": True},
    "facebook-recruiting-iii-keyword-extraction": {"gold": 0.79479, "silver": 0.76177, "bronze": 0.71345, "median": 0.60685, "is_lower_better": False},
    "freesound-audio-tagging-2019": {"gold": 0.74399, "silver": 0.7181, "bronze": 0.69233, "median": 0.54819, "is_lower_better": False},
    "google-quest-challenge": {"gold": 0.42278, "silver": 0.39597, "bronze": 0.37496, "median": 0.3572, "is_lower_better": False},
    "google-research-identify-contrails-reduce-global-warming": {"gold": 0.71059, "silver": 0.6936, "bronze": 0.67929, "median": 0.63819, "is_lower_better": False},
    "h-and-m-personalized-fashion-recommendations": {"gold": 0.03354, "silver": 0.02517, "bronze": 0.02394, "median": 0.02177, "is_lower_better": False},
    "herbarium-2020-fgvc7": {"gold": 0.63151, "silver": 0.2805, "bronze": 0.05334, "median": 0.05334, "is_lower_better": False},
    "herbarium-2021-fgvc8": {"gold": 0.54332, "silver": 0.41067, "bronze": 0.13026, "median": 0.05155, "is_lower_better": False},
    "herbarium-2022-fgvc9": {"gold": 0.84602, "silver": 0.75373, "bronze": 0.5965, "median": 0.22549, "is_lower_better": False},
    "histopathologic-cancer-detection": {"gold": 0.9835, "silver": 0.9798, "bronze": 0.9738, "median": 0.9477, "is_lower_better": False},
    "hms-harmful-brain-activity-classification": {"gold": 0.29081, "silver": 0.35332, "bronze": 0.37538, "median": 0.47383, "is_lower_better": True},
    "hotel-id-2021-fgvc8": {"gold": 0.7205, "silver": 0.39, "bronze": 0.0216, "median": 0.0006, "is_lower_better": False},
    "hubmap-kidney-segmentation": {"gold": 0.9484, "silver": 0.9455, "bronze": 0.9439, "median": 0.0, "is_lower_better": False},
    "icecube-neutrinos-in-deep-ice": {"gold": 0.97731, "silver": 1.00788, "bronze": 1.01857, "median": 1.01996, "is_lower_better": True},
    "imet-2020-fgvc7": {"gold": 0.696, "silver": 0.649, "bronze": 0.649, "median": 0.627, "is_lower_better": False},
    "inaturalist-2019-fgvc6": {"gold": 0.15955, "silver": 0.26058, "bronze": 0.39028, "median": 0.43478, "is_lower_better": True},
    "invasive-species-monitoring": {"gold": 0.99505, "silver": 0.99237, "bronze": 0.98979, "median": 0.96999, "is_lower_better": False},
    "iwildcam-2019-fgvc6": {"gold": 0.212, "silver": 0.129, "bronze": 0.114, "median": 0.108, "is_lower_better": False},
    "iwildcam-2020-fgvc7": {"gold": 0.778, "silver": 0.688, "bronze": 0.594, "median": 0.524, "is_lower_better": False},
    "jigsaw-toxic-comment-classification-challenge": {"gold": 0.9874, "silver": 0.98668, "bronze": 0.98639, "median": 0.98079, "is_lower_better": False},
    "jigsaw-unintended-bias-in-toxicity-classification": {"gold": 0.94608, "silver": 0.94304, "bronze": 0.94088, "median": 0.93417, "is_lower_better": False},
    "kuzushiji-recognition": {"gold": 0.903, "silver": 0.8, "bronze": 0.658, "median": 0.5985, "is_lower_better": False},
    "leaf-classification": {"gold": 0.0, "silver": 0.00791, "bronze": 0.01526, "median": 0.10834, "is_lower_better": True},
    "learning-agency-lab-automated-essay-scoring-2": {"gold": 0.83583, "silver": 0.83518, "bronze": 0.83471, "median": 0.82827, "is_lower_better": False},
    "lmsys-chatbot-arena": {"gold": 0.98392, "silver": 0.99277, "bronze": 1.00283, "median": 1.05212, "is_lower_better": True},
    "ml2021spring-hw2": {"gold": 0.76705, "silver": 0.76261, "bronze": 0.76105, "median": 0.72566, "is_lower_better": False},
    "mlsp-2013-birds": {"gold": 0.93527, "silver": 0.90038, "bronze": 0.87372, "median": 0.86572, "is_lower_better": False},
    "movie-review-sentiment-analysis-kernels-only": {"gold": 0.69344, "silver": 0.68095, "bronze": 0.6732, "median": 0.6415, "is_lower_better": False},
    "multi-modal-gesture-recognition": {"gold": 0.13304, "silver": 0.1769, "bronze": 0.24926, "median": 0.322, "is_lower_better": True},
    "new-york-city-taxi-fare-prediction": {"gold": 2.83377, "silver": 2.88191, "bronze": 2.92371, "median": 3.59741, "is_lower_better": True},
    "nfl-player-contact-detection": {"gold": 0.78167, "silver": 0.72203, "bronze": 0.69652, "median": 0.69139, "is_lower_better": False},
    "nomad2018-predict-transparent-conductors": {"gold": 0.05589, "silver": 0.06229, "bronze": 0.06582, "median": 0.06988, "is_lower_better": True},
    "osic-pulmonary-fibrosis-progression": {"gold": -6.8412, "silver": -6.8533, "bronze": -6.8683, "median": -6.8993, "is_lower_better": False},
    "paddy-disease-classification": {"gold": 0.98732, "silver": 0.98617, "bronze": 0.98387, "median": 0.96889, "is_lower_better": False},
    "petfinder-pawpularity-score": {"gold": 16.95041, "silver": 17.06636, "bronze": 17.0971, "median": 17.70298, "is_lower_better": True},
    "plant-pathology-2020-fgvc7": {"gold": 0.97836, "silver": 0.97465, "bronze": 0.97361, "median": 0.94852, "is_lower_better": False},
    "plant-pathology-2021-fgvc8": {"gold": 0.8612, "silver": 0.85305, "bronze": 0.83508, "median": 0.75445, "is_lower_better": False},
    "plant-seedlings-classification": {"gold": 0.99244, "silver": 0.98614, "bronze": 0.98236, "median": 0.95591, "is_lower_better": False},
    "playground-series-s3e18": {"gold": 0.66088, "silver": 0.65988, "bronze": 0.6588, "median": 0.64603, "is_lower_better": False},
    "predict-volcanic-eruptions-ingv-oe": {"gold": 3971366.0, "silver": 4808057.0, "bronze": 4999330.0, "median": 6300677.0, "is_lower_better": True},
    "random-acts-of-pizza": {"gold": 0.97908, "silver": 0.76482, "bronze": 0.6921, "median": 0.5996, "is_lower_better": False},
    "ranzcr-clip-catheter-line-classification": {"gold": 0.97357, "silver": 0.97152, "bronze": 0.9709, "median": 0.9675, "is_lower_better": False},
    "rsna-2022-cervical-spine-fracture-detection": {"gold": 0.2767, "silver": 0.49, "bronze": 0.5212, "median": 0.5223, "is_lower_better": True},
    "rsna-breast-cancer-detection": {"gold": 0.49, "silver": 0.43, "bronze": 0.41, "median": 0.28, "is_lower_better": False},
    "rsna-miccai-brain-tumor-radiogenomic-classification": {"gold": 0.60096, "silver": 0.5815, "bronze": 0.57449, "median": 0.52553, "is_lower_better": False},
    "seti-breakthrough-listen": {"gold": 0.79806, "silver": 0.78095, "bronze": 0.77439, "median": 0.75889, "is_lower_better": False},
    "siim-covid19-detection": {"gold": 0.623, "silver": 0.609, "bronze": 0.601, "median": 0.586, "is_lower_better": False},
    "siim-isic-melanoma-classification": {"gold": 0.9455, "silver": 0.9401, "bronze": 0.937, "median": 0.9128, "is_lower_better": False},
    "smartphone-decimeter-2022": {"gold": 1.768, "silver": 2.119, "bronze": 3.068, "median": 3.328, "is_lower_better": True},
    "spaceship-titanic": {"gold": 0.82066, "silver": 0.81388, "bronze": 0.80967, "median": 0.79565, "is_lower_better": False},
    "spooky-author-identification": {"gold": 0.16506, "silver": 0.26996, "bronze": 0.29381, "median": 0.41879, "is_lower_better": True},
    "stanford-covid-vaccine": {"gold": 0.34728, "silver": 0.35175, "bronze": 0.3534, "median": 0.3631, "is_lower_better": True},
    "statoil-iceberg-classifier-challenge": {"gold": 0.11374, "silver": 0.13753, "bronze": 0.14552, "median": 0.20371, "is_lower_better": True},
    "tabular-playground-series-dec-2021": {"gold": 0.9566, "silver": 0.95658, "bronze": 0.95658, "median": 0.95342, "is_lower_better": False},
    "tabular-playground-series-may-2022": {"gold": 0.99823, "silver": 0.99822, "bronze": 0.99818, "median": 0.97267, "is_lower_better": False},
    "tensorflow-speech-recognition-challenge": {"gold": 0.90485, "silver": 0.89627, "bronze": 0.88793, "median": 0.77722, "is_lower_better": False},
    "tensorflow2-question-answering": {"gold": 0.68578, "silver": 0.62872, "bronze": 0.61913, "median": 0.59639, "is_lower_better": False},
    "text-normalization-challenge-english-language": {"gold": 0.99724, "silver": 0.99135, "bronze": 0.99038, "median": 0.99037, "is_lower_better": False},
    "text-normalization-challenge-russian-language": {"gold": 0.99012, "silver": 0.98232, "bronze": 0.97592, "median": 0.97591, "is_lower_better": False},
    "tgs-salt-identification-challenge": {"gold": 0.89097, "silver": 0.87163, "bronze": 0.85918, "median": 0.81665, "is_lower_better": False},
    "the-icml-2013-whale-challenge-right-whale-redux": {"gold": 0.98961, "silver": 0.95017, "bronze": 0.90521, "median": 0.86521, "is_lower_better": False},
    "tweet-sentiment-extraction": {"gold": 0.72689, "silver": 0.71752, "bronze": 0.71705, "median": 0.71378, "is_lower_better": False},
    "us-patent-phrase-to-phrase-matching": {"gold": 0.87, "silver": 0.863, "bronze": 0.8616, "median": 0.851, "is_lower_better": False},
    "uw-madison-gi-tract-image-segmentation": {"gold": 0.87917, "silver": 0.87139, "bronze": 0.86699, "median": 0.85499, "is_lower_better": False},
    "ventilator-pressure-prediction": {"gold": 0.1119, "silver": 0.1338, "bronze": 0.1364, "median": 0.1638, "is_lower_better": True},
    "vesuvius-challenge-ink-detection": {"gold": 0.77993, "silver": 0.72525, "bronze": 0.66003, "median": 0.41844, "is_lower_better": False},
    "vinbigdata-chest-xray-abnormalities-detection": {"gold": 0.289, "silver": 0.257, "bronze": 0.243, "median": 0.223, "is_lower_better": False},
    "whale-categorization-playground": {"gold": 0.56236, "silver": 0.44852, "bronze": 0.40515, "median": 0.32788, "is_lower_better": False},
}


def get_medal_thresholds(competition_id: str) -> dict | None:
    """Look up medal score thresholds for a competition.

    Returns a dict with keys: gold, silver, bronze, median, is_lower_better.
    Returns None if the competition is not in the lookup table.
    """
    return MEDAL_THRESHOLDS.get(competition_id)
