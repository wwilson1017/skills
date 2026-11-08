// A made-up grill: a lunch-order tablet for an office break room. Build it with
//   python3 ../build.py . --title "Lunch Board Grill · v1" --what "Six decisions about the break-room lunch board"
const PAGE = 'lunch-board', VERSION = 1;          // PAGE is stable across rounds; bump VERSION each round
// const MULTI = true;                             // several people answer: adds a required name field
// Topics this round cannot ask yet: they depend on the answers above and come in round 2.
const NEXT = [
  'When the e-mail goes out, once the closing time (B2) is settled',
  'What the board shows on days the café is closed, and who keeps that list',
  'Whether anyone pays lunch back, which decides if the cost tally (C2) matters',
];
const SECTIONS = [
  {k:'A', t:'Who and how', take:'Keep it open to everyone and quick to start; nobody manages accounts.'},
  {k:'B', t:'The order screen', take:'One screen and an early close leave room to fix mistakes before the café\'s cutoff.'},
  {k:'C', t:'Getting it to the café', take:'The board sends the order itself; a person gets a copy, not a job.'},
];
const Q = [
  {id:'A1', s:'A', t:'Who can order?', why:'About 42 people eat in on a normal day, and visitors join roughly twice a month. Keeping a staff list current costs more than the odd extra sandwich.', o:[
    ['everyone', 'Everyone on site', 'No list to keep up.', 1],
    ['staff', 'Staff only', 'Someone keeps the staff list current.']]},
  {id:'A2', s:'A', t:'How does someone say who they are?', why:'Orders under the wrong name happen about once a month on the paper sheet today, so a simple name list is enough to start.', vis:'vis-signin', o:[
    ['name', 'Tap your name on a list', 'Fast. Anyone could tap someone else\'s name.', 1],
    ['badge', 'Scan your badge', 'Needs a reader on the tablet.'],
    ['pin', 'Type a 4-digit PIN', 'People forget PINs, and someone has to reset them.']]},
  {id:'B1', s:'B', t:'What does the order screen look like?', why:'The menu has 14 items, and most people order the same thing every week. One screen keeps a normal order to three taps.', vis:'vis-order', o:[
    ['one', 'One screen: the menu, tap, done', 'Three taps for a regular order.', 1],
    ['steps', 'Step by step: main, then side, then drink', 'Slower, but fewer mistakes on a big menu.']]},
  {id:'B2', s:'B', t:'When does ordering close?', why:'The café stops taking orders at 10:00. Closing at 9:30 leaves half an hour to fix a wrong order or a failed e-mail.', vis:'vis-timeline', o:[
    ['0930', '9:30', 'A half-hour buffer before the café\'s cutoff.', 1],
    ['1000', '10:00, the café\'s own cutoff', 'No slack if anything goes wrong.'],
    ['eve', 'The evening before', 'Plans ahead, but people forget.']]},
  {id:'C1', s:'C', t:'Who sends the order to the café?', why:'Today someone retypes the paper sheet into an e-mail, which takes about 25 minutes a day and causes most of the 3 wrong orders a week.', vis:'vis-flow', o:[
    ['auto', 'The board e-mails it at 9:30 by itself', 'Nobody retypes; the office manager gets a copy.', 1],
    ['person', 'The office manager presses Send', 'A person checks it first, and it waits when they\'re out.']]},
  {id:'C2', s:'C', t:'Extras in the first version', multi:true, why:'Tick every one you want. Leaving it blank takes the starred one.', o:[
    ['repeat', '"Same as last time" button', 'About 6 in 10 orders repeat the week before.', 1],
    ['diet', 'Dietary tags on the menu', 'Vegetarian, gluten-free and so on.'],
    ['tally', 'A weekly cost tally per person', 'Only matters if people pay lunch back.']]},
];
