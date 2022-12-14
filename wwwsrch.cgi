#!/usr/bin/perl

# =================================================================
# 名前: WwwSearch 4.0
# 機能: サイトの内容を検索するCGIスクリプト。
# 種別：フリーソフト（私用・商用問わず、利用・改造・流用・再配布可）
# 作者: 杜甫々
# 参照: https://www.tohoho-web.com/
# =================================================================

# =================================================================
# カスタマイズパラメータ
# =================================================================

# ★ Perlのパス名
# 1行目の #!/usr/local/bin/perl の行を、使用しているプロバイダやサーバー
# の環境にあわせて変更してください。

# ★ 検索対象フォルダ
# 検索対象のフォルダ名を指定してください。http://～ のようなURLを指定す
# ることはできません。複数指定する場合は ('../dir1', '../dir2') の様に
# 指定してください。ドットドット(..)は「ひとつ上のフォルダ」を意味します。
@target_dirs = ('../introkouza', '../blog', ../member);

# ★ 除外ディレクトリ
# 検索対象から除外するフォルダ名を指定してください
@exclude_dirs = ('../../lng');

# ★ 検索対象ファイル
# 検索対象とするファイルの拡張子を指定します。.htm や .txt などのテキスト
# ファイルのみ指定できます。.doc や .xls などの専用アプリケーションが必要
# なものは指定できません。
@suffix = (".htm", ".html", ".png", .jpg, .svg);

# ★ 下位フォルダ回帰検索フラグ
# 下位のフォルダを回帰的に検索する場合は1を指定してください。
$recursive_flag = 1;

# ★ [戻る]ボタン
# [戻る]のリンクをクリックされた時にジャンプする先のページを指定して
# ください。http://～ ではじまるURLも指定可能です。
$return_url = 'https://intro-3i/';

# ★ 検索対象ファイルの文字コード
# 検索対象のファイルの漢字コードを指定してください。シフトJISの場合は "sjis"、
# EUCの場合は "euc"、UTF-8の場合は "utf-8" を指定してください。混在している
# 場合や不明な場合は "unknown" を指定してください。ただし、unknown を指定し
# た場合は負荷が高くなり検索も遅くなります。
$charset = "utf-8";

# ★文字コード自動判別対象行数
# $charset を "unknown" とした場合、コードの自動判別を行うために参照する行数
# を指定します。この数が大きいと判別が正確になりますが、性能は劣化します。
$code_guess_line = 20;

# ★ 検索結果ヒントの表示行数
# 検索結果に、ファイルの内容のヒントとして表示する行数を指定します。
$how_many_lines = 2;			# マッチした行の前後何行を表示するか

# ★ デバッグモード
# デバッグを行う場合は1を指定してください。
$debug_mode = 0;

# ★ ロギングフラグ
# wwwsrch.log ファイルにロギングを行う場合は 1 を指定してください。
$do_logging = 1;

# ★ ログファイル名
# ロギングを行うファイル名 wwwsrch.log を変更したい場合に変更してください。
$logging_file = "wwwsrch.log";

# ★ ファイル名表示
# 検索結果のタイトルの横にファイル名を表示する場合は1を、表示しない場合は0を
# 指定してください。
$print_filename = 0;

# ★最大検索対象ファイル数
# 検索するファイルの最大数を指定してください。0を指定すると無制限になります。
$max_search_count = 0;

# ★タイトル
# 検索ページのタイトルを指定してください。
$page_title = "検索";

# =================================================================
# 本体
# =================================================================
use Encode;
use Encode::Guess;

# 出力をバッファリングしないようにするためのおまじない
$| = 1;				

# 検索した件数
$search_count = 0;

# ヒットした件数
$found_count = 0;

# ヘッダ部を書き出す
print <<"EOF";
Content-Type: text/html

<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>$page_title</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="stylesheet" href="style.css">
</head>
<body>
<h1>$page_title</h1>
EOF

# wwwsrch.cgi?test で呼ばれたときはテストを実行して終了する
if ("$ARGV[0]" eq "test") {
	doTest();
} else {
	doMain();
}

# フッタを書き出す
print <<EOF;
<script>
document.getElementById("word").focus();
</script>
</body>
</html>
EOF

#
# メインルーチン
#
sub doMain {

	# フォームから検索文字列を読み込む
	$word = readForm();

	# 戻るボタンを書き出す
	if ($return_url ne "") {
		print "<div class='return-url'><a href='$return_url'>[戻る]</a></div>\n";
	}

	# フォームを書き出す
	print "<form method='POST' action='wwwsrch.cgi'>\n";
	print "  <input type='text' name='word' id='word' value='" . html($word) . "'>\n";
	print "  <button>検索</button>\n";
	print "</form>\n";

	# 検索する
	if ($word ne "") {

		# 検索文字列をログに追加する
		if ($do_logging) {
			logging($word);
		}

		# 検索用語を分解しておく
		@words = split(/ +/, $word);
		foreach $w (@words) {
			$WORD{$w} = 1;
			if ($w =~ /[\x80-\xff]/) {
				# マルチバイト文字をを使用しているフラグ
				$WORD_MBFLAG{$w} = 1;
			} else {
				# マルチバイト文字をを使用しているフラグ
				$WORD_MBFLAG{$w} = 0;
				# 正規表現のメタ文字を無効化した文字列
				$tmp = $w;
				$tmp =~ s/([\+\*\.\?\^\$\[\-\]\|\(\)\\])/\\$1/g;
				$WORD_NOMETA{$w} = $tmp;
			}
		}

		# 検索する
		print "<dl>\n";
		foreach $dir (@target_dirs) {
			searchDir($dir);
		}
		print "</dl>\n";

		# 検索された件数を書き出す
		print "<hr>\n";
		if ($found_count) {
			print "<div class='result'>$found_count 件みつかりました。</div>\n";
		} else {
			print "<div class='result'>1件もみつかりませんでした。</div>\n";
		}

		# 最大検索ファイル数を超えている場合はその旨を表示する。
		if ($search_count > $max_search_count) {
			print "<div class='max_search_count'>最大検索対象ファイル数 $max_search_count ファイルを超えたので中断します。</div>\n";
		}
	}
}

#
# すべてのファイルをなめ回す
#
sub searchDir {
	local($dir) = $_[0];
	local(@filelist, $file, $filename);
	opendir(DIR, $dir);
	@filelist = readdir(DIR);
	closedir(DIR);
	foreach $file (@filelist) {
		if ($file eq ".") { next; }
		if ($file eq "..") { next; }
		$filename = "$dir/$file";
		if (-d $filename) {
			if ($recursive_flag) {
				&searchDir($filename);
			}
		} else {
			&searchFile($filename, $dir);
		}
	}
}

#
# ファイルの中身を検索する
#
sub searchFile {
	local($target, $tdir) = @_;
	# 指定していない拡張子のファイルは無視する
	$fname = substr($target, rindex($target, "."));
	if ((grep { $_ eq $fname } @suffix) == 0) {
		return;
	}

	# 除外対象ディレクトリであれば除外する
	foreach $exc (@exclude_dirs) {
		if ($exc !~ /\/$/) {
			$exc = $exc . "/";
		}
		if ($exc eq substr($target, 0, length($exc))) {
			return;
		}
	}

	# 最大検索対象数を超えていれば終了する
	$search_count++;
	if ($max_search_count != 0) {
		if ($search_count > $max_search_count) {
			return;
		}
	}

	# 各種変数を初期化する
	undef %wordflag;
	$title = "";
	$match_count = 0;

	# ファイルを読み込む
	open(IN, $target);
	@lines = <IN>;
	close(IN);

	# ファイルの文字コードを得る
	if ($charset eq "unknown") {
		$code = getCode(*lines);
	} else {
		$code = $charset;
	}

	# デバッグ文
	if ($debug_mode) {
		print "<dt>検索中：$search_count: $target ($code)...<br>\n";
	}

	# UTF-8に変換する
	if ($code ne "utf-8") {
		for ($i = 0; $i <= $#lines; $i++) {
			$lines[$i] = encode("utf-8", decode($code, $lines[$i]));
		}
	}

	# Macの \r 改行のファイルに対する考慮
	if (($#lines == 0) && ($lines[0] =~ /\r[^\n]/)) {
		@lines = split(/\r/, $lines[0]);
	}

	# それぞれの行に対し・・・
	loop: for ($i = 0; $i <= $#lines; $i++) {
		$line = $lines[$i];

		# タイトルを覚えておく
		if (($title eq "") && ($line =~ /<title>/i)) {
			$title = $line;
		}

		# それぞれの検索語に対して・・・
		foreach $word (@words) {
			# すでに見つかっているなら次の行
			if ($wordflag{$word} == 1) { next; }

			# 検索語が見つからないなら次の行
			if ($WORD_MBFLAG{$word}) {
				if (index($line, $word) == -1) { next; }
			} else {
				if ($line !~ /$WORD_NOMETA{$word}/i) { next; }
			}

			# HTMLをとりはずしてもマッチするか調べる
			$text = $line;
			$text =~ s/<[^>]*(>|$)//g;
			if ($WORD_MBFLAG{$word}) {
				if (index($text, $word) == -1) { next; }
			} else {
				if ($text !~ /$WORD_NOMETA{$word}/i) { next; }
			}

			# 見つかったことを覚えておく
			$wordflag{$word} = 1;

			# URL置換を行う
			# $target =~ s|○○○|△△△|;

			# ページタイトルを表示する
			$found_count++;
			$title =~ s/<[^>]*(>|$)//g;
			$title =~ s/[\r\n]+//g;
			if ($title eq "") {
				$title = $target;
			}
			print "<dt><a href=\"$target\" target=\"out\">$title</a>\n";

			# ファイル名を表示する
			if ($print_filename) {
				$target =~ s/$tdir\/?//;
				print "( <a href=\"$target\" target=out>$target</a> )\n";
			}

			# 表示すべき行数を得る
			$imin = $i - $how_many_lines;
			if ($imin < 0) { $imin = 0; }
			$imax = $i + $how_many_lines;
			if ($imax > $#lines) { $imax = $#lines; }

			# 検索にマッチした箇所を表示する
			print "<dd>";
			for ($j = $imin; $j <= $imax; $j++) {
				$line = $lines[$j];
				$line =~ s/<[^>]*(>|$)//g;
				foreach $w (@words) {
					$line =~ s/($w)/<b>$1<\/b>/ig;
				}
				print "$line ";
			}
			print "\n";
			last loop;
		}
	}
}

#
# テストモード
#
sub doTest {
	print "CGIスクリプトは正常に動作しています。... OK<br>\n";
	if ($] >= 5.008) {
		print "Perl バージョンが $] です。... OK<br>\n";
	} else {
		print "Perl バージョンが $] です。... NG<br>\n";
		print "Perl 5.8.0 以上が必要です。<br>\n";
	}
	if ($do_logging) {
		if (-w $logging_file) {
			print "$logging_file に書き込み可能です。... OK<br>\n";
		} else {
			print "$logging_file に書き込みできません。... NG<br>\n";
		}
	}
}

#
# フォームからの入力データを読み込み検索文字列を返却する
#
sub readForm {
	my $qs, @a, $x, $name, $value, %FORM;

	if ($ENV{'REQUEST_METHOD'} eq "POST") {
		read(STDIN, $qs, $ENV{'CONTENT_LENGTH'});
	} else {
		$qs = $ENV{'QUERY_STRING'};
	}
	@a = split(/&/, $qs);
	foreach $x (@a) {
		($name, $value) = split(/=/, $x);
		$value =~ tr/+/ /;
		$value =~ s/%([0-9a-fA-F][0-9a-fA-F])/pack("C", hex($1))/eg;
		$FORM{$name} = $value;
	}
	if (defined($FORM{'word'})) {
		return $FORM{'word'};
	} else {
		return "";
	}
}

#
# HTMLサニタイジング
#
sub html {
	local($msg) = $_[0];
	$msg =~ s/&/&amp;/g;
	$msg =~ s/</&lt;/g;
	$msg =~ s/>/&gt;/g;
	$msg =~ s/"/&quot;/g;
	$msg =~ s/'/&#39;/g;
	$msg =~ s/ /&nbsp;/g;
	return $msg;
}

#
# 検索した用語をロギングする
#
sub logging {
	local($word) = @_;
	my ($sec, $min, $hour, $mday, $mon, $year) = localtime(time);
	open(OUT, ">> $logging_file");
	printf(OUT "%04d-%02d-%02d %02d:%02d:%02d %s %s\n",
			$year + 1900, $mon + 1, $mday, $hour, $min, $sec,
			$ENV{'REMOTE_ADDR'}, $word);
	close(OUT);
}

#
# 文字コードを自動判別する
#
sub getCode {
	local(*lines) = @_;
	my $line = "";
	for (my $i = 0; $i < $code_guess_line; $i++) {
		$line .= $lines[$i];
	}
	my $enc = guess_encoding($line, qw/euc-jp shift_jis 7bit-jis utf-8/);
	$enc = (ref $enc) ? $enc->name : $enc;
	if ($enc =~ /euc-jp/) {
		return "euc-jp";
	} elsif ($enc =~ /shiftjis/) {
		return "shiftjis";
	} elsif ($enc =~ /jis/) {
		return "7bit-jis";
	} else {
		return "utf-8";
	}
}
