const fs = require('fs');
const f = 'D:/workspace/golden-shovel-app-devlop-安卓/golden-shovel-app-devlop-安卓/pages/explore/callOrderEdit/callOrderEdit.vue';
let c = fs.readFileSync(f, 'utf8');

const oldStr = "\t\t/** 播放/暂停语音 */\r\n\t\ttogglePlayVoice() {\r\n\t\t\t// 诊断：弹出提示确认函数是否被执行\r\n\t\t\tuni.showModal({\r\n\t\t\t\ttitle: '诊断',\r\n\t\t\t\tcontent: '试听按钮被点击了！voicePath长度=' + (this.voicePath && this.voicePath.length) + ' isPlaying=' + this.isPlaying,\r\n\t\t\t\tshowCancel: false\r\n\t\t\t});\r\n\t\t\tif (this.isPlaying) {";

const newStr = "\t\t/** 播放/暂停语音 */\r\n\t\ttogglePlayVoice() {\r\n\t\t\tif (this.isPlaying) {";

if (c.includes(oldStr)) {
	c = c.replace(oldStr, newStr);
	fs.writeFileSync(f, c, 'utf8');
	console.log('OK: replaced successfully');
} else {
	console.log('FAIL: old string not found');
	// try with \n only
	const oldStr2 = oldStr.replace(/\r\n/g, '\n');
	if (c.includes(oldStr2)) {
		c = c.replace(oldStr2, newStr.replace(/\r\n/g, '\n'));
		fs.writeFileSync(f, c, 'utf8');
		console.log('OK: replaced successfully (LF mode)');
	} else {
		console.log('FAIL: also not found in LF mode');
	}
}
