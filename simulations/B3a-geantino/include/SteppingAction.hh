/// \file SteppingAction.hh
/// \brief Geantino Labs (IFPR), nov/2026 — grava cada passo no TrajectoryRecorder

#ifndef GeantinoSteppingAction_h
#define GeantinoSteppingAction_h 1

#include "G4UserSteppingAction.hh"

namespace Geantino
{

class SteppingAction : public G4UserSteppingAction
{
  public:
    SteppingAction() = default;
    ~SteppingAction() override = default;

    void UserSteppingAction(const G4Step* step) override;
};

}  // namespace Geantino

#endif
