// Round 2 of the made-up lunch-board grill. Build it with the round-1 answers locked in:
//   python3 ../../build.py . --title "Lunch Board Grill · v2" --what "Two follow-ups and one decision worth recording" --locked ../answers-v1.json
const PAGE = 'lunch-board', VERSION = 2;
const SECTIONS = [
  {k:'D', t:'Follow-ups', take:'Your later close and your holiday question opened two new questions. Everything else, including your own-words answer on A2, is locked.'},
  {k:'E', t:'Worth writing down', take:'One round-1 decision is hard to undo and would puzzle someone later. Most rounds have none.'},
];
const Q = [
  {id:'D1', s:'D', t:'You moved the close to 10:00. When does the board send the order?', why:'The café\'s cutoff is also 10:00, so the e-mail has to leave the minute the board closes. If it fails, there\'s no time left to phone the order in.', o:[
    ['0955', 'Close and send at 9:55', 'Keeps your later close, with five minutes to spare.', 1],
    ['1000', 'Close and send at 10:00 exactly', 'Counts on the café reading its e-mail a minute late.'],
    ['back', 'Go back to 9:30', 'My first recommendation.']]},
  {id:'D2', s:'D', t:'Who enters the days the café is closed?', why:'The café closes about eight days a year and e-mails its closures a month ahead.', o:[
    ['om', 'The office manager, once a month', 'About two minutes a month.', 1],
    ['none', 'Nobody: people find out when the café doesn\'t deliver', 'No upkeep, but 42 people miss lunch.']]},
  // A decision card: an ADR candidate. Only for a decision that passes all three gates; gates are one line each, in this order.
  {id:'E1', s:'E', kind:'adr', t:'Record it: orders are kept under a name, not a badge number',
   text:'Orders are stored under the name a person taps, because nobody wanted to buy a badge reader for a lunch list. Badges can be added later as a second way to pick the same name.',
   gates:['Every saved order and the "same as last time" button are keyed on the name.',
          'The office already has badges, so a reader on the tablet is what most people would expect.',
          'Names start today with no hardware; badges stop wrong-name orders, about one a month.'],
   why:'You answered A2 in your own words: names now, badges if it becomes a problem.'},
];
