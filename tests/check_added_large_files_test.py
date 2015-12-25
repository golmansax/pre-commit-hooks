from __future__ import absolute_import
from __future__ import unicode_literals

import subprocess

import pytest

from pre_commit_hooks.check_added_large_files import find_large_added_files
from pre_commit_hooks.check_added_large_files import main
from pre_commit_hooks.util import cmd_output
from testing.util import cwd
from testing.util import write_file


def test_nothing_added(temp_git_dir):
    with cwd(temp_git_dir):
        assert find_large_added_files(['f.py'], 0) == 0


def test_adding_something(temp_git_dir):
    with cwd(temp_git_dir):
        write_file('f.py', "print('hello world')")
        cmd_output('git', 'add', 'f.py')

        # Should fail with max size of 0
        assert find_large_added_files(['f.py'], 0) == 1


def test_add_something_giant(temp_git_dir):
    with cwd(temp_git_dir):
        write_file('f.py', 'a' * 10000)

        # Should not fail when not added
        assert find_large_added_files(['f.py'], 0) == 0

        cmd_output('git', 'add', 'f.py')

        # Should fail with strict bound
        assert find_large_added_files(['f.py'], 0) == 1

        # Should also fail with actual bound
        assert find_large_added_files(['f.py'], 9) == 1

        # Should pass with higher bound
        assert find_large_added_files(['f.py'], 10) == 0


def test_added_file_not_in_pre_commits_list(temp_git_dir):
    with cwd(temp_git_dir):
        write_file('f.py', "print('hello world')")
        cmd_output('git', 'add', 'f.py')

        # Should pass even with a size of 0
        assert find_large_added_files(['g.py'], 0) == 0


def test_integration(temp_git_dir):
    with cwd(temp_git_dir):
        assert main(argv=[]) == 0

        write_file('f.py', 'a' * 10000)
        cmd_output('git', 'add', 'f.py')

        # Should not fail with default
        assert main(argv=['f.py']) == 0

        # Should fail with --maxkb
        assert main(argv=['--maxkb', '9', 'f.py']) == 1


def has_gitlfs():
    output = cmd_output('git', 'lfs', retcode=None, stderr=subprocess.STDOUT)
    return 'git lfs status' in output


@pytest.mark.xfail(not has_gitlfs(), reason='This test requires git-lfs')
def test_allows_git_lfs(temp_git_dir):  # pragma: no cover
    with cwd(temp_git_dir):
        # Work around https://github.com/github/git-lfs/issues/913
        cmd_output('git', 'commit', '--allow-empty', '-m', 'foo')
        cmd_output('git', 'lfs', 'install')
        write_file('f.py', 'a' * 10000)
        cmd_output('git', 'lfs', 'track', 'f.py')
        cmd_output('git', 'add', '.')
        # Should succeed
        assert main(('--maxkb', '9', 'f.py')) == 0
