import re


def process_incident(raw_text):
  # 1. Scrub phone numbers, emails, and 7-digit student IDs, but KEEP room numbers
  scrubbed = re.sub(
      r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE REDACTED]', raw_text
  )
  scrubbed = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL REDACTED]', scrubbed)
  scrubbed = re.sub(r'\b\d{7}\b', '[ID REDACTED]', scrubbed)

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
    category = 'RA Next-Shift (Noise/Policy)'
    urgency = 'Low'

  return {'scrubbed_text': scrubbed, 'category': category, 'urgency': urgency}