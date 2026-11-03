import unittest

from backend.conversation import advance, new_state


class ConversationTests(unittest.TestCase):
    def event(self, text='', location=None, media=None, id='event-1'):
        return {'id': id, 'text': text, 'location': location, 'media': media or []}

    def test_three_messages_complete_one_draft_and_pin_needs_confirmation(self):
        state = new_state()
        state, _ = advance(state, self.event('KETERANGAN: Api membakar pohon sejak sore', media=['photo-id']))
        self.assertEqual(state['status'], 'draft')
        state, reply = advance(state, self.event(location={'latitude': -1, 'longitude': 110}, id='pin'))
        self.assertFalse(state['location_confirmed'])
        self.assertIn('KONFIRMASI LOKASI 1', reply)
        state, reply = advance(state, self.event('KONFIRMASI LOKASI 1', id='confirm'))
        self.assertEqual(state['status'], 'complete')
        self.assertIn('belum diverifikasi', reply.lower())
        self.assertFalse(state['consent_contact'])

    def test_replacing_pin_invalidates_previous_confirmation(self):
        state = new_state()
        state, _ = advance(state, self.event(location={'latitude': -1, 'longitude': 110}))
        state, _ = advance(state, self.event('KONFIRMASI LOKASI 1'))
        state, _ = advance(state, self.event(location={'latitude': -2, 'longitude': 111}))
        state, _ = advance(state, self.event('KONFIRMASI LOKASI 1'))
        self.assertFalse(state['location_confirmed'])
        self.assertEqual(state['location_version'], 2)

    def test_contact_decline_does_not_block_report_and_plain_yes_is_not_consent(self):
        state = new_state()
        state, _ = advance(state, self.event('ya'))
        self.assertFalse(state['consent_contact'])
        state, _ = advance(state, self.event('IZIN KONTAK TIDAK'))
        self.assertFalse(state['consent_contact'])
        self.assertIs(state['consent_record'], False)

    def test_max_four_questions_without_new_facts_then_resume_after_input(self):
        state = new_state()
        for _ in range(6):
            state, _ = advance(state, self.event('halo'))
        self.assertEqual(state['questions_count'], 4)
        self.assertEqual(state['status'], 'held')
        state, _ = advance(state, self.event(media=['valid-media']))
        self.assertEqual(state['status'], 'draft')
        self.assertEqual(state['questions_count'], 1)

    def test_commands_are_not_description_and_new_report_requires_choice(self):
        state = new_state()
        state, reply = advance(state, self.event('REPORT'))
        self.assertTrue(state['pending_new'])
        self.assertIn('BARU', reply)
        self.assertIsNone(state['description'])
        state, _ = advance(state, self.event('LANJUT'))
        self.assertFalse(state['pending_new'])

    def test_invalid_media_never_counts_as_complete(self):
        state = new_state()
        state, reply = advance(state, self.event('KETERANGAN: Ada api membakar pohon'))
        self.assertEqual(state['media_ids'], [])
        self.assertIn('foto atau video', reply.lower())
