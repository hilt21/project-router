"""Verify saved replay artifacts and measurable limits; never run a model or grade meaning."""
import argparse
import hashlib
import json
from pathlib import Path


def check(manifest_path):
    root = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text())
    if manifest['real_work_fresh_chat'] != 'not-run':
        raise ValueError('This packet replay cannot certify a fresh Work project chat')
    results = []
    for case in manifest['cases']:
        files = {}
        for key, item in case['files'].items():
            path = (root / item['path']).resolve()
            if not path.is_relative_to(root):
                raise ValueError('Replay artifact escapes its directory')
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                raise ValueError(f"Artifact changed: {item['path']}")
            files[key] = path
        packet = files['packet'].read_text()
        metadata, _ = json.JSONDecoder().raw_decode(packet[packet.index('{'):])
        if metadata['source']['sha'] != case['source_sha'] or metadata['source']['kind'] != 'git-commit':
            raise ValueError('Packet must identify its actual immutable local source')
        if metadata['project_id'] != 'content-studio' or metadata['mode'] != case['mode']:
            raise ValueError('Wrong project or platform packet')
        if metadata['mutations_authorized'] or metadata['intended_actions']:
            raise ValueError('These replays only request copy and visual plans')
        if case['mode'] == 'wechat':
            output = json.loads(files['output'].read_text())
            size = len(''.join(output['wechat_body'].split()))
            visuals = output['visuals']
            if len(visuals) != 2:
                raise ValueError('The historical task requested two visual plans')
            if any(v.get('aspect_ratio', v.get('format', {}).get('aspect_ratio')) != '3:4' for v in visuals):
                raise ValueError('Unexpected visual aspect ratio')
            metric = 'body_non_whitespace_characters'
        else:
            body = files['output'].read_text().split('\nSource:', 1)[0]
            size = len(body.split())
            metric = 'body_whitespace_words'
        lower, upper = case['body_range']
        if not lower <= size <= upper:
            raise ValueError(f"Body outside requested range: {case['id']} = {size}")
        results.append({'id': case['id'], metric: size, 'status': 'passed'})
    return {'status': 'passed', 'layer': 'saved-content-artifacts', 'cases': results,
            'semantic_correctness': 'not-verified-by-script', 'distribution_effect': 'unknown',
            'image_generation': 'not-run', 'publication': 'not-run'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path,
                        default=Path(__file__).parent / 'probes/content-dhh/manifest.json')
    args = parser.parse_args()
    print(json.dumps(check(args.manifest), ensure_ascii=False, indent=2))
