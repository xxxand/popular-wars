var global = (function() {
    return this
})();
if (!global && typeof GameGlobal !== 'undefined') global = GameGlobal;
var pluginInfoMap = {};;
global.requirePlugin = global.requirePlugin || function(path) {
    var position = path.indexOf('/');
    var alias = '';
    var pagePath = '';
    if (position !== -1) {
        alias = path.substr(0, position);
        pagePath = path.substr(position + 1, path.length);
    } else {
        alias = path;
    }
    if (pluginInfoMap.hasOwnProperty(alias)) {
        var realPath = '';
        if (pagePath.length === 0) {
            realPath = '__plugin__/' + pluginInfoMap[alias].appid;
            return require(realPath);
        } else {
            realPath = '__plugin__/' + pluginInfoMap[alias].appid + '/' + pagePath;
            return require(realPath);
        }
    } else {
        console.error('not found alias: ', alias);
        throw new Error('Plugin ' + alias + ' is not defined.')
    }
};
define("opendata/index.js", function(require, module, exports) {
    (() => {
        "use strict";
        var t = void 0 !== wx.getSharedCanvas ? wx.getSharedCanvas() : wx.createCanvas(),
            e = t.getContext("2d");
        var i = 0,
            n = 0,
            r = 1,
            o = 1;

        function a(e) {
            i = e.screenX, n = e.screenY, r = t.width / c, o = t.height / c
        }
        var s = wx.getSystemInfoSync(),
            c = 750 / s.screenWidth,
            u = (s.screenHeight, new Set),
            h = new Set,
            f = new Set,
            l = new Set;
        wx.onTouchStart((function(t) {
            var e = t.changedTouches[0],
                a = e.clientX - i;
            if (a < 0 || a > r) return;
            var s = e.clientY - n;
            if (s < 0 || s > o) return;
            d = !0, u.forEach((function(t) {
                t(a * c, s * c)
            }))
        })), wx.onTouchMove((function(t) {
            if (!d) return;
            var e = t.changedTouches[0],
                r = e.clientX - i,
                o = e.clientY - n;
            h.forEach((function(t) {
                t(r * c, o * c)
            }))
        })), wx.onTouchEnd((function(t) {
            if (!d) return;
            d = !1;
            var e = t.changedTouches[0],
                r = e.clientX - i,
                o = e.clientY - n;
            f.forEach((function(t) {
                t(r * c, o * c)
            }))
        })), wx.onTouchCancel((function(t) {
            if (!d) return;
            d = !1;
            var e = t.changedTouches[0],
                r = e.clientX - i,
                o = e.clientY - n;
            l.forEach((function(t) {
                t(r * c, o * c)
            }))
        }));
        var d = !1;
        var p = [1, 1.33, 1.66, 2],
            v = .02,
            y = .998,
            g = Math.log(y);
        const m = function() {
            function t(t) {
                this.target = t, this.$scrollFactor = 1, this.previousTime = 0, this.velocity = 0, this.previousVelocity = [], this.currentPosition = 0, this.previousPosition = 0, this.lastPoint = 0, this.started = !0
            }
            return t.prototype.start = function(t) {
                this.started = !0, this.velocity = 0, this.previousVelocity.length = 0, this.previousPosition = this.currentPosition = t, this.lastPoint = t, this.animation = void 0
            }, t.prototype.update = function(t) {
                this.currentPosition = t;
                var e = this.lastPoint - t,
                    i = e + this.target.scrollV;
                this.lastPoint = t, (i < 0 || i > this.target.maxScrollV) && (i -= .5 * e), this.target.scrollV = i
            }, t.prototype.finish = function() {
                var t = this.target,
                    e = t.scrollV,
                    i = t.maxScrollV;
                this.started = !1;
                for (var n = 2.33 * this.velocity, r = this.previousVelocity, o = r.length, a = 2.33, s = 0; s < o; s++) {
                    var c = p[s];
                    n += r[0] * c, a += c
                }
                var u = n / a,
                    h = Math.abs(u);
                if (h > v) {
                    var f = 0,
                        l = e + (u - v) / g * 2 * this.$scrollFactor;
                    if (l < 0 || l > i)
                        for (l = e; Math.abs(u) > v;) u *= (l -= u) < 0 || l > i ? .95 * y : y, f++;
                    else f = Math.log(v / h) / g;
                    this.throwTo(l, f)
                } else this.checkScroll()
            }, t.prototype.checkScroll = function() {
                var t = this.target,
                    e = t.scrollV,
                    i = t.maxScrollV;
                e < 0 ? this.throwTo(0, 300) : e > i && this.throwTo(i, 300)
            }, t.prototype.onTick = function(t) {
                var e = t - this.previousTime;
                if (this.previousTime = t, this.started) {
                    var i = this.previousVelocity;
                    i.length >= 4 && i.shift(), this.velocity = (this.currentPosition - this.previousPosition) / e, i.push(this.velocity), this.previousPosition = this.currentPosition
                }
                this.animation && (this.animation.update(e), this.target.scrollV = this.animation.value, this.animation.isEnd && (this.animation = void 0, this.checkScroll()))
            }, t.prototype.throwToTop = function() {
                this.throwTo(0, 300)
            }, t.prototype.throwTo = function(t, e) {
                var i = this.target.scrollV;
                i !== t && (this.animation = new w(i, t, e))
            }, t
        }();
        var w = function() {
            function t(t, e, i) {
                this.from = t, this.to = e, this.duration = i, this.pass = 0, this.value = 0, this.isEnd = !1, this.distance = e - t, this.value = t
            }
            return t.prototype.update = function(t) {
                var e, i;
                this.pass += t, this.pass > this.duration ? (this.value = this.to, this.isEnd = !0) : this.value = (e = this.pass / this.duration, ((i = e - 1) * i * i + 1) * this.distance + this.from)
            }, t
        }();
        Object.create;

        function S(t, e) {
            var i = "function" == typeof Symbol && t[Symbol.iterator];
            if (!i) return t;
            var n, r, o = i.call(t),
                a = [];
            try {
                for (;
                    (void 0 === e || e-- > 0) && !(n = o.next()).done;) a.push(n.value)
            } catch (t) {
                r = {
                    error: t
                }
            } finally {
                try {
                    n && !n.done && (i = o.return) && i.call(o)
                } finally {
                    if (r) throw r.error
                }
            }
            return a
        }
        Object.create;
        "function" == typeof SuppressedError && SuppressedError;
        var x = /\ud83c[\udffb-\udfff](?=\ud83c[\udffb-\udfff])|(?:[^\ud800-\udfff][\u0300-\u036f\ufe20-\ufe23\u20d0-\u20f0]?|[\u0300-\u036f\ufe20-\ufe23\u20d0-\u20f0]|(?:\ud83c[\udde6-\uddff]){2}|[\ud800-\udbff][\udc00-\udfff]|[\ud800-\udfff])[\ufe0e\ufe0f]?(?:[\u0300-\u036f\ufe20-\ufe23\u20d0-\u20f0]|\ud83c[\udffb-\udfff])?(?:\u200d(?:[^\ud800-\udfff]|(?:\ud83c[\udde6-\uddff]){2}|[\ud800-\udbff][\udc00-\udfff])[\ufe0e\ufe0f]?(?:[\u0300-\u036f\ufe20-\ufe23\u20d0-\u20f0]|\ud83c[\udffb-\udfff])?)*/g;
        const T = function() {
            function t(t) {
                if ("string" != typeof t) throw new Error("Input must be a string");
                this._string = t, this._match = t.match(x) || []
            }
            return Object.defineProperty(t.prototype, "length", {get: function() {
                    return this._match.length
                },
                enumerable: !1,
                configurable: !0
            }), t.prototype.reverse = function() {
                return this._match.reverse().join("")
            }, t.prototype.substring = function(t, e) {
                var i;
                void 0 === t && (t = 0);
                var n, r = this.length,
                    o = (parseInt(t, 10) || 0) < 0 ? 0 : parseInt(t, 10) || 0;
                return o > r && (o = r), (n = void 0 === e ? r : (parseInt(e, 10) || 0) < 0 ? 0 : parseInt(e, 10) || 0) > r && (n = r), o > n && (o = (i = S([n, o], 2))[0], n = i[1]), this._match.slice(o, n).join("")
            }, t.prototype.substr = function(t, e) {
                void 0 === t && (t = 0);
                var i, n = this.length,
                    r = parseInt(t, 10) || 0;
                return r >= n || e <= 0 ? "" : (r < 0 && (r = Math.max(0, r + n)), i = void 0 === e ? n : r + (parseInt(e, 10) || 0), this._match.slice(r, i).join(""))
            }, t
        }();
        var k, _, b, V = "grad-dev",
            P = "skin-dev",
            E = "entity-dev";

        function I(t, e, i, n, r, o) {
            for (var a = e.split(""), s = "", c = 0; c < a.length; c++) {
                var u = s + a[c],
                    h = t.measureText(u);
                if (!h) return void t.fillText(e, i, n, r);
                h.width > r && c > 0 ? (t.fillText(s, i, n), s = a[c], n += o) : s = u
            }
            t.fillText(s, i, n)
        }

        function M(t, e) {
            return K[e] ? Promise.resolve(K[e]) : (D[e] || (D[e] = new Promise((function(i, n) {
                var r = wx.createImage();
                r.src = t, r.onload = function() {
                    K[e] = r, delete D[e], i(r)
                }, r.onerror = function() {
                    console.error("未加载到素材 ".concat(t)), delete D[e], n()
                }
            }))), D[e])
        }
        for (var K = {}, D = {}, C = 1; C <= 3; C++) M("res/opendata/rank_".concat(C, ".png"), C);
        M("res/opendata/default_avatar.png", "default_avatar");
        var A = 81,
            F = 70,
            j = ["#549bff", "#959fad"],
            H = function() {
                function i(i) {
                    var n, r = this;
                    this.data = [], this.totalData = [], this.touchScroll = new m(this), this.avatars = {}, this.dataKey = "grad", this.render = function(i) {
                        if (!r._isDisposed) {
                            if (r.touchScroll.onTick(i), r._dirty)
                                if (r._dirty = !1, e.clearRect(0, 0, t.width, t.height), r.data.length)
                                    for (var n = 0, o = r.data.length; n < o; n++) r.drawItem(n);
                                else e.fillStyle = "#ffffff", e.font = "40px simHei", e.textAlign = "center", I(e, "rank" === r.type ? "噢！还没有好友进入排行榜。" : "噢！这里还没有人进入排行榜。", t.width / 2, t.height / 2, 750, 68);
                            requestAnimationFrame(r.render)
                        }
                    }, this._scrollV = 0, this.maxScrollV = 0, this._dirty = !0, this.onTouchStart = function(t, e) {
                        r.touchScroll.start(e)
                    }, this.onTouchMove = function(t, e) {
                        r.touchScroll.update(e)
                    }, this.onTouchEnd = function(t, e) {
                        r.touchScroll.finish()
                    }, this._isDisposed = !1, this.type = i.type, this.dataKey = i.dataKey, e.clearRect(0, 0, t.width, t.height), "rank" === i.type ? (i.refresh && (_ = void 0), n = _ ? Promise.resolve(_) : (b || (console.log("*opendata* getFriendCloudStorage... <".concat(V, "> <").concat(P, ">")), b = new Promise((function(t, e) {
                        wx.getFriendCloudStorage({
                            keyList: [V, P],
                            success: function(e) {
                                b = void 0, _ = e.data, t(e.data)
                            },
                            fail: function(t) {
                                return e(t.errMsg)
                            },
                            complete: function() {
                                return console.log("*opendata* getFriendCloudStorage complete")
                            }
                        })
                    }))), b)) : n = new Promise((function(t, e) {
                        wx.getGroupCloudStorage({
                            shareTicket: i.shareTicket,
                            keyList: [V, P, E],
                            success: function(e) {
                                return t(e.data)
                            },
                            fail: function(t) {
                                return e(t.errMsg)
                            }
                        })
                    })), n.then((function(t) {
                        if (!r._isDisposed) {
                            var e, i = r.totalData = t.map((function(t) {
                                var e = function(t) {
                                    var e = {};
                                    return t.forEach((function(t) {
                                        return e[t.key] = Number(t.value)
                                    })), e
                                }(t.KVDataList);
                                return {
                                    rank: 0,
                                    name: t.nickname,
                                    avatar: t.avatarUrl,
                                    grad: e[V],
                                    skin: e[P],
                                    entity: 0 | e[E]
                                }
                            }));
                            (i = i.filter((function(t) {
                                return t[r.dataKey] >= 0
                            }))).sort((function(t, e) {
                                    return e[r.dataKey] - t[r.dataKey]
                                })), i.forEach((function(t, e) {
                                    return t.rank = e + 1
                                })), r.data = i, e = r.onTouchStart, u.add(e),
                                function(t) {
                                    h.add(t)
                                }(r.onTouchMove),
                                function(t) {
                                    f.add(t)
                                }(r.onTouchEnd),
                                function(t) {
                                    l.add(t)
                                }(r.onTouchEnd), r.maxScrollV = r._calcMaxScrollV(), requestAnimationFrame((function(t) {
                                    r.touchScroll.previousTime = t, requestAnimationFrame(r.render)
                                }))
                        }
                    })).catch((function(i) {
                        console.error(i), e.fillStyle = "#000000", e.font = "60px simHei", e.textAlign = "center", I(e, i, t.width / 2, t.height / 2, 750, 68)
                    }))
                }
                return i.prototype.update = function(t) {
                    var e = this;
                    this.dataKey = t.dataKey;
                    var i = this.totalData;
                    (i = i.filter((function(t) {
                        return t[e.dataKey] > 0
                    }))).sort((function(t, i) {
                        return i[e.dataKey] - t[e.dataKey]
                    })), i.forEach((function(t, e) {
                        return t.rank = e + 1
                    })), this.data = i, this.maxScrollV = this._calcMaxScrollV(), this.touchScroll.throwToTop(), this._dirty = !0
                }, i.prototype._calcMaxScrollV = function() {
                    return Math.max(0, 91 * this.data.length - 10 - t.height + 0 + 15)
                }, Object.defineProperty(i.prototype, "scrollV", {get: function() {
                        return this._scrollV
                    },
                    set: function(t) {
                        this._scrollV = t, this._dirty || (this._dirty = !0)
                    },
                    enumerable: !1,
                    configurable: !0
                }), i.prototype.dispose = function() {
                    var t;
                    this._isDisposed = !0, this.avatars = {}, t = this.onTouchStart, u.delete(t),
                        function(t) {
                            h.delete(t)
                        }(this.onTouchMove),
                        function(t) {
                            f.delete(t)
                        }(this.onTouchEnd),
                        function(t) {
                            l.delete(t)
                        }(this.onTouchEnd)
                }, i.prototype.drawItem = function(i) {
                    var n = this,
                        r = -this._scrollV + 91 * i + 0;
                    if (!(r > t.height || r + A < 0)) {
                        var o = this.data[i];
                        e.fillStyle = i % 2 == 0 ? j[0] : j[1], e.fillRect(0, r, 750, A), K[o.rank] ? e.drawImage(K[o.rank], 31.5, 9.5 + r) : (e.fillStyle = "#000000", o.rank < 1e4 ? e.font = "".concat(40, "px simHei") : e.font = "".concat(Math.floor(160 / o.rank.toString().length), "px simHei"), e.textAlign = "center", e.fillText(o.rank.toString(), 54, 63 + r)), e.strokeStyle = "#000000", e.strokeRect(109, 5.5 + r + 1, 68, 68);
                        var a = o.avatar;
                        if (a && "" !== a) {
                            var s = this.avatars[o.avatar];
                            s ? e.drawImage(s, 108, 5.5 + r, F, F) : ((s = this.avatars[o.avatar] = wx.createImage()).src = o.avatar, s.onload = function() {
                                n._dirty || (n._dirty = !0)
                            })
                        } else e.drawImage(K.default_avatar, 108, 5.5 + r, F, F);
                        if (e.fillStyle = "#000000", e.font = "".concat(28, "px simHei"), e.textAlign = "left", e.fillText(function(t, e, i, n) {
                                void 0 === n && (n = "...");
                                var r = t.measureText(e);
                                if (!r) return e;
                                var o = r.width;
                                if (o > i) {
                                    var a = new T(e),
                                        s = a.length;
                                    do {
                                        if (s <= 0) {
                                            e = "";
                                            break
                                        }
                                        e = a.substr(0, --s), o = t.measureText(e + n).width
                                    } while (o > i);
                                    e += n
                                }
                                return e
                            }(e, o.name, 400), 200, 58 + r), "grad" === this.dataKey) {
                            var c = function(t) {
                                for (var e = 0, i = 0; i < k.length && t >= k[i][0]; i++) e = i;
                                return k[e][1]
                            }(o.grad);
                            (u = K[c]) ? e.drawImage(u, 450, .5 + r): M("res/opendata/".concat(c, ".png"), c).then((function() {
                                n._dirty || (n._dirty = !0)
                            })).catch((function() {}))
                        } else if ("skin" === this.dataKey) {
                            (u = K.skin_point) ? e.drawImage(u, 450, .5 + r): M("res/opendata/skin_point.png", "skin_point").then((function() {
                                n._dirty || (n._dirty = !0)
                            })).catch((function() {}))
                        } else {
                            var u;
                            (u = K.head) ? e.drawImage(u, 450, .5 + r): M("res/opendata/head.png", "head").then((function() {
                                n._dirty || (n._dirty = !0)
                            })).catch((function() {}))
                        }
                        e.fillStyle = "#000000", e.font = "".concat(46, "px simHei"), e.textAlign = "right", e.fillText(o[this.dataKey].toString(), 645, 62 + r)
                    }
                }, i
            }();
        const R = H;
        var X;
        wx.onMessage((function(t) {
            if ("setRankKeySuffix" === t.type) return e = t.key, V = "grad".concat(e), P = "skin".concat(e), E = "entity".concat(e), console.info("*grad key*:", V), console.info("*skin key*:", P), void console.info("*entity key*:", E);
            var e;
            if ("setGradData" !== t.type)
                if ("hide" !== t.type)
                    if (X && X.type === t.type) X.update(t);
                    else switch (X && X.dispose(), t.type) {
                        case "rank":
                        case "groupRank":
                            a(t), X = new R(t);
                            break;
                        default:
                            console.warn("未知的message类型", t)
                    } else X && (X.dispose(), X = void 0);
            else ! function(t) {
                k = t.gradData
            }(t)
        }))
    })();
});
require("opendata/index.js");