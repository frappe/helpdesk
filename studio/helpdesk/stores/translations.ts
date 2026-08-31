import { computed, ref } from 'vue'

// Temporary translations for the portal, so switching Language in settings visibly
// changes what the reader sees.
//
// This is a stand-in, not the real thing: helpdesk's own strings live in `.po` files and
// reach the desk through `frappe.translate`, but a Studio page renders its text straight
// from the block tree, with no `__()` between the two. Until those strings are extracted,
// this covers the portal's furniture — the words the reader meets on every screen — for
// the languages a demo is likely to switch to.
//
// The language comes from the `user_lang` cookie, which Frappe sets from the signed-in
// user's own setting — a Studio page is not rendered through the web template that
// stamps `<html lang>`, so that attribute stays "en" whatever the reader picked. The
// settings dialog reloads the page after saving, so the whole portal comes back in the
// new language rather than half-translating in place.

const DICTIONARY: Record<string, Record<string, string>> = {
  hi: {
    // list
    'Tickets': 'टिकट',
    'List': 'सूची',
    'Raise a ticket': 'टिकट बनाएं',
    'ID': 'क्रमांक',
    'Subject': 'विषय',
    'Status': 'स्थिति',
    'First Response': 'पहला उत्तर',
    'Resolution': 'समाधान',
    'Assigned To': 'सौंपा गया',
    'Customer': 'ग्राहक',
    'Priority': 'प्राथमिकता',
    'Type': 'प्रकार',
    'Team': 'टीम',
    'Contact': 'संपर्क',
    'Rating': 'रेटिंग',
    'Created': 'बनाया गया',
    // ticket
    'Ticket Type': 'टिकट प्रकार',
    'App': 'ऐप',
    'Reference module': 'संदर्भ मॉड्यूल',
    'Sub reference module': 'उप संदर्भ मॉड्यूल',
    'Type a message': 'संदेश लिखें',
    'Send': 'भेजें',
    'Discard': 'रद्द करें',
    'Feedback Rating': 'प्रतिक्रिया रेटिंग',
    'Did this solve your issue?': 'क्या इससे आपकी समस्या हल हुई?',
    "Yes, it's fixed": 'हाँ, हल हो गया',
    'No, still an issue': 'नहीं, समस्या बनी है',
    // the lifecycle rail
    'Request received': 'अनुरोध प्राप्त हुआ',
    'Assigned to': 'सौंपा गया',
    'Assigned to agent': 'एजेंट को सौंपा गया',
    'Waiting to be assigned': 'सौंपे जाने की प्रतीक्षा',
    'An agent is on it': 'एक एजेंट देख रहा है',
    'First response': 'पहला उत्तर',
    'Awaiting first response': 'पहले उत्तर की प्रतीक्षा',
    'Awaiting resolution': 'समाधान की प्रतीक्षा',
    'Resolved': 'हल हो गया',
    'Closed': 'बंद',
    'Pending': 'लंबित',
    // settings
    'Personal': 'व्यक्तिगत',
    'Profile': 'प्रोफ़ाइल',
    'Organization': 'संगठन',
    'How you appear across the knowledge base.': 'नॉलेज बेस में आप कैसे दिखते हैं।',
    'Preferences': 'प्राथमिकताएँ',
    'Save': 'सहेजें',
    'Preferences updated successfully.': 'प्राथमिकताएँ सहेजी गईं।',
    'Language': 'भाषा',
    'Change language of the application.': 'ऐप्लिकेशन की भाषा बदलें।',
    'Select language': 'भाषा चुनें',
    'Timezone': 'समय क्षेत्र',
    'Change timezone of the application.': 'ऐप्लिकेशन का समय क्षेत्र बदलें।',
    'Select timezone': 'समय क्षेत्र चुनें',
    'Theme': 'थीम',
    'Switch between light, dark, or system theme.': 'लाइट, डार्क या सिस्टम थीम चुनें।',
    'Conversation layout': 'बातचीत का लेआउट',
    'Read replies as a timeline, or as a chat with your own messages on the right.': 'उत्तर टाइमलाइन में पढ़ें, या चैट की तरह जहाँ आपके संदेश दाईं ओर हों।',
    'Security': 'सुरक्षा',
    'Password': 'पासवर्ड',
    'Change your account password for security.': 'सुरक्षा के लिए अपने खाते का पासवर्ड बदलें।',
    'Change password': 'पासवर्ड बदलें',
    'Manage organization': 'संगठन प्रबंधित करें',
    'Invite people': 'लोगों को आमंत्रित करें',
    'Organization members': 'संगठन के सदस्य',
    'Send Invite': 'आमंत्रण भेजें',
    'Invite by email': 'ईमेल से आमंत्रित करें',
    'New people will be added to the team as': 'नए लोग टीम में जोड़े जाएंगे',
    'Separate multiple emails with commas': 'कई ईमेल अल्पविराम से अलग करें',
    'Members': 'सदस्य',
    'Ticket': 'टिकट',
    'Created': 'बनाया गया',
    'No tickets match your search.': 'आपकी खोज से कोई टिकट मेल नहीं खाता।',
    'Settings': 'सेटिंग्स',
    'Tickets': 'टिकट',
    'No tickets from this organization yet.': 'इस संगठन से अभी कोई टिकट नहीं।',
    'Search': 'खोजें',
    'Last seen': 'अंतिम बार देखा',
    'Role': 'भूमिका',
    'Never': 'कभी नहीं',
    'No members match this filter.': 'इस फ़िल्टर से कोई सदस्य मेल नहीं खाता।',
    'tickets': 'टिकट',
    'members': 'सदस्य',
    'View organization': 'संगठन देखें',
    'Pick an organization to manage its people and settings.': 'लोगों और सेटिंग्स को प्रबंधित करने के लिए एक संगठन चुनें।',
    'Pick an organization to see its people and settings.': 'लोगों और सेटिंग्स देखने के लिए एक संगठन चुनें।',
    'Timeline': 'टाइमलाइन',
    'Chat': 'चैट',
    'Light': 'लाइट',
    'Dark': 'डार्क',
    'System': 'सिस्टम',
  },
  fr: {
    'Tickets': 'Tickets',
    'List': 'Liste',
    'Raise a ticket': 'Créer un ticket',
    'ID': 'Nº',
    'Subject': 'Objet',
    'Status': 'Statut',
    'First Response': 'Première réponse',
    'Resolution': 'Résolution',
    'Assigned To': 'Attribué à',
    'Customer': 'Client',
    'Priority': 'Priorité',
    'Type': 'Type',
    'Team': 'Équipe',
    'Contact': 'Contact',
    'Rating': 'Évaluation',
    'Created': 'Créé le',
    'Ticket Type': 'Type de ticket',
    'App': 'Application',
    'Reference module': 'Module concerné',
    'Sub reference module': 'Sous-module concerné',
    'Type a message': 'Écrivez un message',
    'Send': 'Envoyer',
    'Discard': 'Annuler',
    'Feedback Rating': 'Évaluation',
    'Did this solve your issue?': 'Cela a-t-il résolu votre problème ?',
    "Yes, it's fixed": "Oui, c'est réglé",
    'No, still an issue': 'Non, toujours pas',
    'Request received': 'Demande reçue',
    'Assigned to': 'Attribué à',
    'Assigned to agent': 'Attribué à un agent',
    'Waiting to be assigned': "En attente d'attribution",
    'An agent is on it': "Un agent s'en occupe",
    'First response': 'Première réponse',
    'Awaiting first response': 'En attente de la première réponse',
    'Awaiting resolution': 'En attente de résolution',
    'Resolved': 'Résolu',
    'Closed': 'Clôturé',
    'Pending': 'En attente',
    // settings
    'Personal': 'Personnel',
    'Profile': 'Profil',
    'Organization': 'Organisation',
    'How you appear across the knowledge base.': 'Votre apparence dans la base de connaissances.',
    'Preferences': 'Préférences',
    'Save': 'Enregistrer',
    'Preferences updated successfully.': 'Préférences enregistrées.',
    'Language': 'Langue',
    'Change language of the application.': "Changer la langue de l'application.",
    'Select language': 'Choisir une langue',
    'Timezone': 'Fuseau horaire',
    'Change timezone of the application.': "Changer le fuseau horaire de l'application.",
    'Select timezone': 'Choisir un fuseau horaire',
    'Theme': 'Thème',
    'Switch between light, dark, or system theme.': 'Basculer entre le thème clair, sombre ou système.',
    'Conversation layout': 'Affichage de la conversation',
    'Read replies as a timeline, or as a chat with your own messages on the right.': 'Lire les réponses comme une chronologie, ou comme une discussion avec vos messages à droite.',
    'Security': 'Sécurité',
    'Password': 'Mot de passe',
    'Change your account password for security.': 'Changer le mot de passe de votre compte.',
    'Change password': 'Changer le mot de passe',
    'Manage organization': "Gérer l'organisation",
    'Invite people': 'Inviter des personnes',
    'Organization members': "Membres de l'organisation",
    'Send Invite': "Envoyer l'invitation",
    'Invite by email': 'Inviter par e-mail',
    'New people will be added to the team as': "Les nouvelles personnes rejoindront l'équipe en tant que",
    'Separate multiple emails with commas': 'Séparez les adresses par des virgules',
    'Members': 'Membres',
    'Ticket': 'Ticket',
    'Created': 'Créé le',
    'No tickets match your search.': 'Aucun ticket ne correspond à votre recherche.',
    'Settings': 'Réglages',
    'No tickets from this organization yet.': 'Aucun ticket de cette organisation pour le moment.',
    'Search': 'Rechercher',
    'Last seen': 'Vu pour la dernière fois',
    'Role': 'Rôle',
    'Never': 'Jamais',
    'No members match this filter.': 'Aucun membre ne correspond à ce filtre.',
    'tickets': 'tickets',
    'members': 'membres',
    'View organization': "Voir l'organisation",
    'Pick an organization to manage its people and settings.': 'Choisissez une organisation pour gérer ses membres et ses réglages.',
    'Pick an organization to see its people and settings.': 'Choisissez une organisation pour voir ses membres et ses réglages.',
    'Timeline': 'Chronologie',
    'Chat': 'Discussion',
    'Light': 'Clair',
    'Dark': 'Sombre',
    'System': 'Système',
  },
}

/** What the reader chose — `hi-IN` and `hi` both read as Hindi.
 *
 *  A ref rather than a read of the cookie each time, so choosing a language can swap the
 *  portal's words in place. Every string goes through `t()` inside a computed, so setting
 *  this re-renders them all — which is what saves the settings dialog from reloading the
 *  page, and the reader from watching it blank out and come back. */
export const language = ref(readLanguage().split('-')[0])

/** Told to the portal when the reader picks a new one, before the cookie catches up. */
export function setLanguage(value: string) {
  language.value = (value || 'en').split('-')[0]
}

function readLanguage() {
  const cookie = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith('user_lang='))
  return decodeURIComponent(cookie?.split('=')[1] || '') || document.documentElement.lang || 'en'
}

const words = computed(() => DICTIONARY[language.value] || {})

/** Whatever the dictionary has for this string, or the English it was written in. */
export function t(text: string) {
  return words.value[text] || text
}

/** "Assigned to Rosa Mendez" — the phrase is translated, the name is not. */
export function tFormat(text: string, value: string) {
  return `${t(text)} ${value}`.trim()
}

export function useTranslations() {
  return { t, tFormat, language }
}
