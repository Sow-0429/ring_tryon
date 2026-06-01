package domain

import (
	"errors"
	"math"
)

var jpSizeTable = []struct {
	circumferenceMM float64
	size            int
}{
	{41.0, 1}, {42.0, 2}, {43.0, 3}, {44.0, 4}, {45.0, 5},
	{46.0, 6}, {47.5, 7}, {48.5, 8}, {49.5, 9}, {50.5, 10},
	{51.5, 11}, {52.5, 12}, {53.5, 13}, {54.5, 14}, {55.5, 15},
	{56.5, 16}, {57.5, 17}, {58.5, 18}, {60.0, 19}, {61.0, 20},
	{62.0, 21}, {63.0, 22}, {64.0, 23}, {65.0, 24}, {66.0, 25},
}

// CircumferenceForJPSize は日本の号数(1-25)に対応する基準周囲長(mm)を返す。
// 較正ループの正解ラベル(actual_ring_size_jp → actual_circumference_mm)生成に使う。
// 号数表は本パッケージが唯一の真実の源(ADR-0001)。
func CircumferenceForJPSize(size int) (float64, error) {
	for _, entry := range jpSizeTable {
		if entry.size == size {
			return entry.circumferenceMM, nil
		}
	}
	return 0, errors.New("jp size out of range (1-25)")
}

// RingSize は指輪サイズを表す値オブジェクト。
type RingSize struct {
	circumferenceMM float64
}

func NewRingSize(circumferenceMM float64) (RingSize, error) {
	if circumferenceMM <= 0 {
		return RingSize{}, errors.New("circumference must be positive")
	}
	return RingSize{circumferenceMM: circumferenceMM}, nil
}

func (r RingSize) CircumferenceMM() float64 {
	return r.circumferenceMM
}

// JPSize は日本の号数(1-25)を返す。最も近い号数にマッピングする。
func (r RingSize) JPSize() int {
	closest := jpSizeTable[0]
	minDiff := math.Abs(r.circumferenceMM - closest.circumferenceMM)

	for _, entry := range jpSizeTable[1:] {
		diff := math.Abs(r.circumferenceMM - entry.circumferenceMM)
		// 等距離(tie)のときは安全側の大きい号数を採る。表は昇順なので <= で後勝ち。
		if diff <= minDiff {
			minDiff = diff
			closest = entry
		}
	}
	return closest.size
}

// JPSizeRange は推定号数の±1範囲を返す。1-25にクランプする。
func (ringSize RingSize) JPSizeRange() (int, int) {
	jp := ringSize.JPSize()
	low := jp - 1
	if low < 1 {
		low = 1
	}
	high := jp + 1
	if high > 25 {
		high = 25
	}
	return low, high
}

// USSize は米国サイズを返す。
func (r RingSize) USSize() float64 {
	return math.Round((r.circumferenceMM-36.5)/2.55*10) / 10
}

// EUSize は欧州サイズ(周囲長の四捨五入)を返す。
func (r RingSize) EUSize() int {
	return int(math.Round(r.circumferenceMM))
}
