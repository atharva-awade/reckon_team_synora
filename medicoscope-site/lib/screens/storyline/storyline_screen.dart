import 'dart:math';
import 'package:flutter/material.dart';
import 'package:medicoscope/screens/welcome/welcome_screen.dart';

class StorylineScreen extends StatefulWidget {
  const StorylineScreen({super.key});

  @override
  State<StorylineScreen> createState() => _StorylineScreenState();
}

class _StorylineScreenState extends State<StorylineScreen> {
  final ScrollController _scrollController = ScrollController();
  int _currentFrame = 1;
  double _fraction = 0;
  bool _navigated = false;
  bool _isSkipping = false;

  // Preloading
  double _loadProgress = 0;
  bool _ready = false;
  bool _allLoaded = false;
  late final List<NetworkImage> _providers;
  final Set<int> _cachedFrames = {};

  static const int _totalFrames = 826;
  static const int _batchSize = 30;

  // Matches HTML: body { height: 800vh } → scroll height = 8× viewport
  static const double _scrollMultiplier = 8.0;

  @override
  void initState() {
    super.initState();
    _providers = List.generate(
      _totalFrames,
      (i) => NetworkImage(_framePath(i + 1)),
    );
    _scrollController.addListener(_onScroll);
    WidgetsBinding.instance.addPostFrameCallback((_) => _preloadAll());
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  String _framePath(int frame) =>
      'walkthrough/ezgif-frame-${frame.toString().padLeft(3, '0')}.jpg';

  // ── Preload ────────────────────────────────────────────────────────────────

  Future<void> _preloadAll() async {
    int loaded = 0;

    for (int start = 0; start < _totalFrames; start += _batchSize) {
      if (!mounted) return;
      final end = min(start + _batchSize, _totalFrames);
      final futures = <Future>[];

      for (int i = start; i < end; i++) {
        futures.add(
          precacheImage(_providers[i], context).then((_) {
            _cachedFrames.add(i + 1);
            loaded++;
          }).catchError((_) {
            loaded++;
          }),
        );
      }

      await Future.wait(futures);

      if (mounted) {
        final progress = loaded / _totalFrames;
        setState(() {
          _loadProgress = progress;
          if (!_ready && progress >= 0.15) _ready = true;
        });
      }
    }

    if (mounted) {
      setState(() {
        _allLoaded = true;
        if (!_ready) _ready = true;
      });
    }
  }

  // ── Scroll handler (matches HTML: scrollFraction = scrollTop / maxScroll) ──

  void _onScroll() {
    if (!_ready) return;

    final maxScroll = _scrollController.position.maxScrollExtent;
    if (maxScroll <= 0) return;

    final scrollFraction =
        (_scrollController.offset / maxScroll).clamp(0.0, 1.0);

    // Match HTML: frameIndex = Math.floor(scrollFraction * frameCount)
    final targetFrame =
        (scrollFraction * (_totalFrames - 1)).floor().clamp(0, _totalFrames - 1) + 1;

    // Use exact frame if cached, otherwise nearest cached
    final displayFrame = _cachedFrames.contains(targetFrame)
        ? targetFrame
        : _nearestCachedFrame(targetFrame);

    if (displayFrame != _currentFrame || scrollFraction != _fraction) {
      setState(() {
        _currentFrame = displayFrame;
        _fraction = scrollFraction;
      });
    }

    if (scrollFraction >= 0.99 && !_navigated) {
      _navigated = true;
      Future.delayed(const Duration(milliseconds: 600), _navigateToWelcome);
    }
  }

  int _nearestCachedFrame(int target) {
    if (_cachedFrames.isEmpty) return 1;
    for (int d = 0; d <= 50; d++) {
      if (target + d <= _totalFrames && _cachedFrames.contains(target + d)) {
        return target + d;
      }
      if (target - d >= 1 && _cachedFrames.contains(target - d)) {
        return target - d;
      }
    }
    return _currentFrame;
  }

  // ── Skip (matches HTML: window.scrollTo({ top: max, behavior: 'smooth' }))

  void _startSkip() {
    if (_isSkipping) return;
    setState(() => _isSkipping = true);

    if (!_allLoaded) {
      _waitAndSkip();
      return;
    }
    _doSkip();
  }

  Future<void> _waitAndSkip() async {
    while (!_allLoaded && mounted) {
      await Future.delayed(const Duration(milliseconds: 200));
    }

    if (mounted) _doSkip();
  }

  void _doSkip() {
    if (!_scrollController.hasClients) return;

    final maxScroll = _scrollController.position.maxScrollExtent;
    if (maxScroll <= 0) return;

    final currentOffset = _scrollController.offset;
    final remaining = maxScroll - currentOffset;

    // Scale duration by remaining distance (15s for full, proportional otherwise)
    final ms = ((remaining / maxScroll) * 15000).round().clamp(2000, 15000);

    _scrollController.animateTo(
      maxScroll,
      duration: Duration(milliseconds: ms),
      curve: Curves.linear,
    );
  }

  // ── Navigation ─────────────────────────────────────────────────────────────

  void _navigateToWelcome() {
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, animation, __) => const WelcomeScreen(),
        transitionsBuilder: (_, animation, __, child) =>
            FadeTransition(opacity: animation, child: child),
        transitionDuration: const Duration(milliseconds: 800),
      ),
    );
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final screenHeight = MediaQuery.of(context).size.height;
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      body: Stack(
        children: [
          // Native scroll area — matches HTML: body { height: 800vh }
          SingleChildScrollView(
            controller: _scrollController,
            physics: _ready
                ? const ClampingScrollPhysics()
                : const NeverScrollableScrollPhysics(),
            child: SizedBox(
              width: double.infinity,
              height: screenHeight * _scrollMultiplier,
            ),
          ),

          // Frame image (fixed, doesn't scroll)
          Positioned.fill(
            child: IgnorePointer(
              child: RepaintBoundary(
                child: Image(
                  image: _providers[_currentFrame - 1],
                  fit: BoxFit.cover,
                  gaplessPlayback: true,
                  errorBuilder: (_, __, ___) =>
                      Container(color: const Color(0xFF050505)),
                ),
              ),
            ),
          ),

          // Loading overlay (initial load)
          if (!_ready)
            Positioned.fill(
              child: Container(
                color: const Color(0xFF050505),
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SizedBox(
                        width: 200,
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: _loadProgress,
                            minHeight: 3,
                            backgroundColor: Colors.white.withOpacity(0.1),
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Colors.white.withOpacity(0.7),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Loading experience… ${(_loadProgress * 100).toInt()}%',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.5),
                          fontSize: 13,
                          letterSpacing: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // "Preparing skip…" overlay while waiting for all frames
          if (_isSkipping && !_allLoaded)
            Positioned.fill(
              child: Container(
                color: Colors.black.withOpacity(0.6),
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SizedBox(
                        width: 200,
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: _loadProgress,
                            minHeight: 3,
                            backgroundColor: Colors.white.withOpacity(0.1),
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Colors.white.withOpacity(0.7),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Preparing walkthrough… ${(_loadProgress * 100).toInt()}%',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 13,
                          letterSpacing: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // Skip button
          if (_ready && _fraction < 0.95 && !_isSkipping)
            Positioned(
              bottom: 40,
              right: 40,
              child: _SkipButton(onTap: _startSkip),
            ),

          // Scroll hint
          if (_ready && _fraction < 0.04 && !_isSkipping)
            const Positioned(
              bottom: 100,
              left: 0,
              right: 0,
              child: _ScrollHint(),
            ),

          // Progress bar
          if (_ready)
            Positioned(
              bottom: 0,
              left: 0,
              child: Container(
                height: 2,
                width: screenWidth * _fraction,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.white.withOpacity(0.15),
                      Colors.white.withOpacity(0.7),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ── Skip button ──────────────────────────────────────────────────────────────

class _SkipButton extends StatefulWidget {
  final VoidCallback onTap;
  const _SkipButton({required this.onTap});

  @override
  State<_SkipButton> createState() => _SkipButtonState();
}

class _SkipButtonState extends State<_SkipButton> {
  bool _hovering = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovering = true),
      onExit: (_) => setState(() => _hovering = false),
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(horizontal: 26, vertical: 13),
          decoration: BoxDecoration(
            border: Border.all(
              color: Colors.white.withOpacity(_hovering ? 0.5 : 0.25),
            ),
            borderRadius: BorderRadius.circular(50),
            color: Colors.white.withOpacity(_hovering ? 0.15 : 0.07),
          ),
          transform: _hovering
              ? (Matrix4.identity()..translate(0.0, -2.0))
              : Matrix4.identity(),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'SKIP',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.85),
                  fontSize: 13,
                  letterSpacing: 2.5,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 10),
              Icon(
                Icons.double_arrow_rounded,
                color: Colors.white.withOpacity(0.85),
                size: 16,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Scroll hint ──────────────────────────────────────────────────────────────

class _ScrollHint extends StatelessWidget {
  const _ScrollHint();

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          'SCROLL TO EXPLORE',
          style: TextStyle(
            color: Colors.white.withOpacity(0.6),
            fontSize: 12,
            letterSpacing: 3,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        Icon(
          Icons.keyboard_double_arrow_down_rounded,
          color: Colors.white.withOpacity(0.5),
          size: 28,
        ),
      ],
    );
  }
}
