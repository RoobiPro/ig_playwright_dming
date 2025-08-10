# Calibrated Window Position Implementation

## Overview
The Instagram automation now uses your manually calibrated window position for perfect alignment.

## Calibrated Values
```
X Position: 2312
Y Position: 113
Width: 883
Height: 937
```

## How It Works

### 1. Primary Method: Calibrated Position
- Uses your exact manually positioned values
- Ensures perfect alignment every time
- No guesswork or approximation

### 2. Fallback Method: Dynamic Detection
- Windows API-based monitor detection
- Automatically calculates left half of secondary screen
- Used only if calibrated position fails

### 3. Integration Points

#### Browser Launch (`browser_utils.py`)
- Initial window positioning using Chrome arguments
- Uses calibrated values for precise placement

#### Session Setup (`instagram_automation.py`)
- Post-load fine-tuning with `align_window_to_calibrated_position()`
- JavaScript-based positioning for pixel-perfect alignment

#### Configuration (`config.py`)
- `get_screen_configuration()` - Primary function (uses calibrated by default)
- `get_calibrated_position()` - Returns exact calibrated values
- `get_dynamic_screen_configuration()` - Fallback dynamic detection

## Available Methods

### InstagramAutomation Class
- `align_window_to_calibrated_position()` - Use your exact calibrated position
- `align_window_to_left_half()` - Use dynamic detection
- `center_window_on_secondary_screen()` - Center on secondary screen
- `get_window_position()` - Get current window position
- `set_window_position(x, y, width, height)` - Manual positioning

## Testing

### Test Calibrated Position
```bash
python test_calibrated_position.py
```

### Quick Position Test
```bash
python -c "import config; pos = config.get_calibrated_position(); print(f'Position: {pos}')"
```

## Usage Priority

1. **Default**: Calibrated position (automatic)
2. **Fallback**: Dynamic detection (if calibrated fails)
3. **Manual**: Custom positioning methods

## Benefits

- **Pixel-perfect alignment**: Exactly where you positioned it manually
- **Consistent positioning**: Same position every time
- **No approximation**: No calculations or guesswork
- **Robust fallback**: Dynamic detection if needed
- **Easy recalibration**: Run `get_window_position.py` to update values

## Recalibration

To update the calibrated position:
1. Run `python get_window_position.py`
2. Position window where you want it
3. Press Enter to capture new values
4. Update `CALIBRATED_WINDOW_POSITION` in `config.py`

## Current Status
✅ Calibrated position: (2312, 113) size 883x937
✅ Integration complete
✅ Testing utilities available
✅ Fallback systems in place