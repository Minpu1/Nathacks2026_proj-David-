import re


def process_incident(raw_text):

  # 2. Classify incident category and urgency
  text_lower = raw_text.lower()
  if any(
      word in text_lower
      for word in [
          'fire',
          'door',
          'propped',
          'stranger',
          'smoke',
          'unlocked',
          'glass',
          'wire',
          'flickering',
          'tripping',
      ]
  ):
    category = 'Urgent Safety'
    urgency = 'High'
  elif any(
      word in text_lower
      for word in [
          'leak',
          'broken',
          'light',
          'heat',
          'water',
          'elevator',
          'drain',
          'chute',
          'latch',
      ]
  ):
    category = 'Maintenance'
    urgency = 'Medium'
  else:
    category = 'Noise/Policy'
    urgency = 'Low'

  return {'scrubbed_text': text_lower, 'category': category, 'urgency': urgency}