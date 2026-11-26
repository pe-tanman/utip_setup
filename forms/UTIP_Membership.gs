/**
 * UTIP membership system — Google Form + Sheet + tiny API, all in one Apps Script.
 *
 * What it does
 *   setup()          creates the member sign-up Google Form and its response spreadsheet,
 *                    adds a clean "Members" tab, and installs the on-submit trigger.
 *   onFormSubmit()   upserts the member (by UT EID) into "Members", emails them the
 *                    onboarding links, and pings the officers' Discord channel.
 *   doPost()         a private JSON API (protected by API_TOKEN) used by:
 *                      - the Discord bot   -> action "verify"   (EID -> grant Member role)
 *                      - the pipeline      -> action "sms_list" (opted-in phone numbers)
 *                      - officers          -> action "stats"
 *
 * Install (5 minutes) — see forms/README.md for screenshots-free step-by-step.
 *   1. script.google.com -> New project -> paste this file -> Save.
 *   2. Edit CONFIG below (links, officer webhook).
 *   3. Run setup() once and approve the permissions. Check the log for the form URL.
 *   4. Deploy -> New deployment -> Web app -> Execute as: Me, Who has access: Anyone.
 *      Copy the web-app URL; the API token is printed in the log by setup().
 */

const CONFIG = {
  FORM_TITLE: 'UTIP — Member Sign-Up',
  SHEET_TITLE: 'UTIP Members (do not share)',
  CLUB_NAME: 'UT International Pickleball Club (UTIP)',
  LINKS: {
    discord: 'https://discord.gg/REPLACE_ME',
    luma: 'https://luma.com/REPLACE_ME',
    instagram: 'https://instagram.com/utip_austin',
  },
  // Discord webhook for a private #officer-log channel (optional). Never a public channel:
  // it receives new member names.
  OFFICER_WEBHOOK_URL: '',
  SEND_WELCOME_EMAIL: true,
};

// Question titles double as keys, so keep them stable after launch.
const Q = {
  NAME: 'Full name',
  EID: 'UT EID',
  EMAIL: 'Email',
  PHONE: 'Phone number',
  DISCORD: 'Discord username',
  SMS: 'Text message newsletter',
  STATUS: 'Are you an international or domestic student?',
  HOME: 'Home country / culture you identify with',
  YEAR: 'Classification',
  LEVEL: 'Pickleball experience',
  HEARD: 'How did you hear about UTIP?',
};
const SMS_YES = 'Yes — text me when new events are posted';
const SMS_NO = 'No thanks';
const MEMBER_HEADERS = ['Joined', 'Updated', 'Name', 'EID', 'Email', 'Phone', 'Phone (E.164)', 'Discord username',
  'SMS opt-in', 'Status', 'Home', 'Classification', 'Level', 'Heard from', 'Discord ID (verified)', 'Verified at'];

function setup() {
  const props = PropertiesService.getScriptProperties();
  if (props.getProperty('FORM_ID')) {
    Logger.log('Already set up. Form: %s', FormApp.openById(props.getProperty('FORM_ID')).getPublishedUrl());
    return;
  }
  const form = FormApp.create(CONFIG.FORM_TITLE)
    .setDescription(
      'Welcome to ' + CONFIG.CLUB_NAME + '! International and domestic students are all welcome.\n' +
      'This puts you on our member list (required for registered UT student orgs) and lets our Discord bot verify you. ' +
      'Your info is only seen by officers and is never shared or sold.')
    .setCollectEmail(false)
    .setAllowResponseEdits(true)
    .setLimitOneResponsePerUser(false)
    .setConfirmationMessage('You\'re in! Check your email for next steps: join our Discord and type /verify, then RSVP on Luma.');

  form.addTextItem().setTitle(Q.NAME).setRequired(true);
  form.addTextItem().setTitle(Q.EID).setRequired(true)
    .setHelpText('e.g. abc1234 — used only to confirm you are a UT student.')
    .setValidation(FormApp.createTextValidation()
      .requireTextMatchesPattern('^[A-Za-z]{2,4}[0-9]{2,6}$')
      .setHelpText('That does not look like a UT EID (letters followed by numbers, e.g. abc1234).').build());
  form.addTextItem().setTitle(Q.EMAIL).setRequired(true)
    .setHelpText('Your utexas.edu email is best.')
    .setValidation(FormApp.createTextValidation().requireTextIsEmail().build());
  form.addTextItem().setTitle(Q.PHONE).setRequired(true)
    .setHelpText('US mobile number, e.g. 512-555-0123.')
    .setValidation(FormApp.createTextValidation()
      .requireTextMatchesPattern('^[+]?[0-9 ()\\-.]{10,18}$')
      .setHelpText('Please enter a 10-digit US phone number.').build());
  form.addTextItem().setTitle(Q.DISCORD).setRequired(false)
    .setHelpText('Your Discord username (not display name). No Discord yet? Leave blank — you can still join later.');
  form.addMultipleChoiceItem().setTitle(Q.SMS).setRequired(true)
    .setHelpText('We text when a new event or social is posted (about 1–4 messages/month). ' +
      'Msg & data rates may apply. Reply STOP to unsubscribe or HELP for help at any time. ' +
      'Consent is not required to join the club.')
    .setChoiceValues([SMS_YES, SMS_NO]);
  form.addMultipleChoiceItem().setTitle(Q.STATUS).setRequired(false)
    .setChoiceValues(['International student', 'Domestic student', 'Exchange / visiting student', 'Prefer not to say']);
  form.addTextItem().setTitle(Q.HOME).setRequired(false);
  form.addMultipleChoiceItem().setTitle(Q.YEAR).setRequired(false)
    .setChoiceValues(['Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate / PhD', 'Other']);
  form.addMultipleChoiceItem().setTitle(Q.LEVEL).setRequired(false)
    .setChoiceValues(['Never played', 'Beginner', 'Intermediate', 'Advanced']);
  form.addCheckboxItem().setTitle(Q.HEARD).setRequired(false)
    .setChoiceValues(['Instagram', 'Friend', 'Poster / flyer', 'Discord', 'Org fair / event'])
    .showOtherOption(true);

  const ss = SpreadsheetApp.create(CONFIG.SHEET_TITLE);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  const members = ss.insertSheet('Members');
  members.appendRow(MEMBER_HEADERS);
  members.setFrozenRows(1);
  members.getRange(1, 1, 1, MEMBER_HEADERS.length).setFontWeight('bold');
  const def = ss.getSheetByName('Sheet1');
  if (def) ss.deleteSheet(def);

  ScriptApp.newTrigger('onFormSubmit').forForm(form).onFormSubmit().create();

  const token = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '');
  props.setProperties({ FORM_ID: form.getId(), SHEET_ID: ss.getId(), API_TOKEN: token });

  Logger.log('Form (share this):  %s', form.getPublishedUrl());
  Logger.log('Form (edit):        %s', form.getEditUrl());
  Logger.log('Sheet (private):    %s', ss.getUrl());
  Logger.log('API token (put in discord/bot/.env and pipeline/.env as UTIP_API_TOKEN): %s', token);
  Logger.log('Next: Deploy -> New deployment -> Web app (Execute as me, Anyone) and copy the URL.');
}

/** Prints the API token again if you lose it. */
function showToken() {
  Logger.log(PropertiesService.getScriptProperties().getProperty('API_TOKEN'));
}

function membersSheet_() {
  const id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  return SpreadsheetApp.openById(id).getSheetByName('Members');
}

function toE164_(raw) {
  const digits = String(raw || '').replace(/\D/g, '');
  if (digits.length === 10) return '+1' + digits;
  if (digits.length === 11 && digits[0] === '1') return '+' + digits;
  if (String(raw).trim().startsWith('+') && digits.length >= 8) return '+' + digits;
  return ''; // flagged: officers fix by hand
}

function onFormSubmit(e) {
  const answers = {};
  e.response.getItemResponses().forEach((r) => {
    const v = r.getResponse();
    answers[r.getItem().getTitle()] = Array.isArray(v) ? v.join(', ') : String(v).trim();
  });
  const eid = (answers[Q.EID] || '').toLowerCase();
  const now = new Date();
  const row = [now, now, answers[Q.NAME], eid, answers[Q.EMAIL], answers[Q.PHONE], toE164_(answers[Q.PHONE]),
    (answers[Q.DISCORD] || '').replace(/^@/, ''), answers[Q.SMS] === SMS_YES ? 'YES' : 'NO',
    answers[Q.STATUS] || '', answers[Q.HOME] || '', answers[Q.YEAR] || '', answers[Q.LEVEL] || '', answers[Q.HEARD] || '', '', ''];

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  let isNew = true;
  try {
    const sh = membersSheet_();
    const data = sh.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {
      if (String(data[i][3]).toLowerCase() === eid) {
        row[0] = data[i][0];            // keep original join date
        row[14] = data[i][14];          // keep Discord verification
        row[15] = data[i][15];
        sh.getRange(i + 1, 1, 1, row.length).setValues([row]);
        isNew = false;
        break;
      }
    }
    if (isNew) sh.appendRow(row);
  } finally {
    lock.releaseLock();
  }

  const first = String(answers[Q.NAME] || '').split(/\s+/)[0];
  if (CONFIG.SEND_WELCOME_EMAIL && answers[Q.EMAIL]) {
    MailApp.sendEmail({
      to: answers[Q.EMAIL],
      subject: 'Welcome to UTIP, ' + first + '! Your next 2 steps',
      htmlBody:
        '<p>Hi ' + first + ',</p><p>Thanks for joining the <b>' + CONFIG.CLUB_NAME + '</b>! You are on the member list. Two quick steps:</p>' +
        '<ol><li><b>Join our Discord:</b> <a href="' + CONFIG.LINKS.discord + '">' + CONFIG.LINKS.discord + '</a><br>' +
        'Then type <code>/verify</code> (or press the Verify button in #verify) and enter your EID to unlock member channels.</li>' +
        '<li><b>RSVP for this week on Luma:</b> <a href="' + CONFIG.LINKS.luma + '">' + CONFIG.LINKS.luma + '</a></li></ol>' +
        (answers[Q.SMS] === SMS_YES ? '<p>You opted in to text alerts. Reply STOP to any text to unsubscribe.</p>' : '') +
        '<p>Follow us on Instagram for announcements: <a href="' + CONFIG.LINKS.instagram + '">' + CONFIG.LINKS.instagram + '</a></p>' +
        '<p>See you on the court!<br>— UTIP officers</p>',
    });
  }
  if (CONFIG.OFFICER_WEBHOOK_URL) {
    UrlFetchApp.fetch(CONFIG.OFFICER_WEBHOOK_URL, {
      method: 'post', contentType: 'application/json', muteHttpExceptions: true,
      payload: JSON.stringify({
        username: 'UTIP Forms',
        content: (isNew ? '🆕 New member: **' : '✏️ Updated member: **') + answers[Q.NAME] + '** (' +
          (answers[Q.STATUS] || 'status n/a') + (answers[Q.HOME] ? ', ' + answers[Q.HOME] : '') + ')',
      }),
    });
  }
}

/** JSON API. POST body: {"token": "...", "action": "verify" | "sms_list" | "stats", ...} */
function doPost(e) {
  let body = {};
  try { body = JSON.parse(e.postData.contents); } catch (err) { return json_({ ok: false, error: 'bad_json' }); }
  const token = PropertiesService.getScriptProperties().getProperty('API_TOKEN');
  if (!token || body.token !== token) return json_({ ok: false, error: 'unauthorized' });

  const sh = membersSheet_();
  const data = sh.getDataRange().getValues();
  const rows = data.slice(1);

  if (body.action === 'verify') {
    const eid = String(body.eid || '').trim().toLowerCase();
    for (let i = 0; i < rows.length; i++) {
      if (String(rows[i][3]).toLowerCase() === eid && eid) {
        sh.getRange(i + 2, 15, 1, 2).setValues([[String(body.discord_id || ''), new Date()]]);
        if (!rows[i][7] && body.discord_name) sh.getRange(i + 2, 8).setValue(body.discord_name);
        return json_({ ok: true, member: true, first_name: String(rows[i][2]).split(/\s+/)[0], status: rows[i][9], level: rows[i][12] });
      }
    }
    return json_({ ok: true, member: false });
  }
  if (body.action === 'sms_list') {
    const list = rows.filter((r) => r[8] === 'YES' && r[6]).map((r) => ({ name: String(r[2]).split(/\s+/)[0], phone: r[6] }));
    return json_({ ok: true, count: list.length, recipients: list });
  }
  if (body.action === 'stats') {
    const count = (fn) => rows.filter(fn).length;
    return json_({
      ok: true, members: rows.length,
      international: count((r) => /international|exchange/i.test(r[9])),
      domestic: count((r) => /domestic/i.test(r[9])),
      sms_opt_in: count((r) => r[8] === 'YES'),
      discord_verified: count((r) => r[14]),
    });
  }
  return json_({ ok: false, error: 'unknown_action' });
}

function doGet() {
  return json_({ ok: true, service: 'utip-members', hint: 'POST only' });
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

/** Handy for the UT roster: exports Name, EID, Email of all members to a new tab. */
function exportRosterForHornsLink() {
  const sh = membersSheet_();
  const rows = sh.getDataRange().getValues().slice(1).map((r) => [r[2], r[3], r[4]]);
  const ss = sh.getParent();
  const out = ss.getSheetByName('Roster export') || ss.insertSheet('Roster export');
  out.clear();
  out.getRange(1, 1, 1, 3).setValues([['Name', 'EID', 'Email']]);
  if (rows.length) out.getRange(2, 1, rows.length, 3).setValues(rows);
}
