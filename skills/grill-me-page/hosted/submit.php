<?php
// grill-me-page collector, the hosted adapter. Same API as collect.py:
//   POST appends one JSON line to answers.jsonl (never web-readable, see .htaccess);
//   GET ?page=&version= returns the newest record whose data matches (?final=1, ?client=, ?name= narrow it);
//   GET ?acks=1 returns the session's acks plus `alive`, the watcher heartbeat.
// Acks (ack-received.json, ack-applied.json) and the heartbeat (watch-alive.json) are written beside the page by
// the session over SSH or SFTP, never through the web, so nobody with the link can fake a green light.
header('Content-Type: application/json');
header('X-Robots-Tag: noindex');
header('Cache-Control: no-store');
header('Access-Control-Allow-Origin: *');  // other sites' forms may post here (same storage, same rules); remove if yours do not
$f = __DIR__ . '/answers.jsonl';
$m = $_SERVER['REQUEST_METHOD'];
if ($m === 'GET') {
  if (isset($_GET['acks'])) {
    $acks = [];
    foreach (['received' => 'ack-received.json', 'applied' => 'ack-applied.json', 'alive' => 'watch-alive.json'] as $k => $name) {
      $p = __DIR__ . '/' . $name;
      if (is_readable($p)) $acks[$k] = json_decode(file_get_contents($p));
    }
    echo $acks ? json_encode($acks) : '{}';
    exit;
  }
  $lines = is_readable($f) ? (file($f, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: []) : [];
  $page = isset($_GET['page']) ? $_GET['page'] : null;
  $version = isset($_GET['version']) ? (string)$_GET['version'] : null;
  $client = isset($_GET['client']) ? $_GET['client'] : null;
  $name = isset($_GET['name']) && $_GET['name'] !== '' ? strtolower(trim($_GET['name'])) : null;
  for ($i = count($lines) - 1; $i >= 0; $i--) {
    $rec = json_decode($lines[$i], true);
    $d = is_array($rec) && isset($rec['data']) && is_array($rec['data']) ? $rec['data'] : null;
    if ($d === null) continue;
    if ($page !== null && (!isset($d['page']) || $d['page'] !== $page)) continue;
    if ($version !== null && (!isset($d['version']) || (string)$d['version'] !== $version)) continue;
    if (isset($_GET['final']) && empty($d['final'])) continue;
    if ($client !== null && (!isset($d['client_id']) || $d['client_id'] !== $client)) continue;
    if ($name !== null && strtolower(trim(isset($d['name']) ? $d['name'] : '')) !== $name) continue;
    echo $lines[$i];
    exit;
  }
  echo '{}';
  exit;
}
if ($m !== 'POST') { http_response_code(405); echo '{"ok":false}'; exit; }
$body = file_get_contents('php://input', false, null, 0, 300001);
if (strlen($body) > 300000) { http_response_code(413); echo '{"ok":false}'; exit; }
$data = json_decode($body);
if (!is_object($data)) { http_response_code(400); echo '{"ok":false}'; exit; }  // a JSON object, not a list or scalar
$ok = file_put_contents($f, json_encode(['at' => gmdate('c'), 'data' => $data]) . "\n", FILE_APPEND | LOCK_EX) !== false;
echo json_encode(['ok' => $ok, 'at' => gmdate('c')]);
