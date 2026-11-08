// Round 2 of the made-up lunch-board grill. Build it with the round-1 answers locked in:
//   python3 ../../build.py . --title "Lunch Board Grill · v2" --what "Two follow-ups on the lunch board" --locked ../answers-v1.json
const PAGE = 'lunch-board', VERSION = 2;
const SECTIONS = [
  {k:'D', t:'Follow-ups', take:'Your later close and your holiday question opened two new questions. Everything else, including your own-words answer on A2, is locked.'},
];
const Q = [
  {id:'D1', s:'D', t:'You moved the close to 10:00. When does the board send the order?', why:'The café\'s cutoff is also 10:00, so the e-mail has to leave the minute the board closes. If it fails, there\'s no time left to phone the order in.', o:[
    ['0955', 'Close and send at 9:55', 'Keeps your later close, with five minutes to spare.', 1],
    ['1000', 'Close and send at 10:00 exactly', 'Counts on the café reading its e-mail a minute late.'],
    ['back', 'Go back to 9:30', 'My first recommendation.']]},
  {id:'D2', s:'D', t:'Who enters the days the café is closed?', why:'The café closes about eight days a year and e-mails its closures a month ahead.', o:[
    ['om', 'The office manager, once a month', 'About two minutes a month.', 1],
    ['none', 'Nobody: people find out when the café doesn\'t deliver', 'No upkeep, but 42 people miss lunch.']]},
];
